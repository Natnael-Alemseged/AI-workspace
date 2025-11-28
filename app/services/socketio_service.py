"""Socket.IO service for real-time chat."""
import os
import uuid
from typing import Optional

import socketio
from dotenv import load_dotenv
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db import AsyncSessionLocal
from app.models.user import User, PushSubscription
from app.models.channel import TopicMember, TopicMessage, Topic
from app.services.notification_service import notification_service
from datetime import datetime

# Load environment variables
load_dotenv(override=True)
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"

# Create Socket.IO server with async support
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # Configure this based on your CORS requirements
    logger=True,
    engineio_logger=True
)


async def get_user_from_token(token: str) -> Optional[User]:
    """
    Authenticate user from JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        User object if authenticated, None otherwise
    """
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience="fastapi-users:auth"
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Fetch user from database
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.id == uuid.UUID(user_id))
            )
            user = result.scalar_one_or_none()
            
            if user and user.is_active:
                return user
            return None
            
    except JWTError as e:
        logger.error(f"JWT decode error in Socket.IO: {e}")
        return None
    except Exception as e:
        logger.error(f"Error authenticating user in Socket.IO: {e}")
        return None


# Store active connections: {sid: user_id}
active_connections = {}

# Store user rooms: {user_id: set(room_ids)}
user_rooms = {}


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection."""
    try:
        # Extract token from auth data
        if not auth or "token" not in auth:
            logger.warning(f"Connection attempt without token: {sid}")
            await sio.disconnect(sid)
            return False
        
        token = auth["token"]
        user = await get_user_from_token(token)
        
        if not user:
            logger.warning(f"Invalid token for connection: {sid}")
            await sio.disconnect(sid)
            return False
        
        # Store connection
        active_connections[sid] = str(user.id)
        user_rooms[str(user.id)] = set()
        
        # Join user to their personal room for receiving global alerts
        personal_room = f"user_{user.id}"
        await sio.enter_room(sid, personal_room)
        logger.info(f"User {user.id} joined personal room: {personal_room}")
        
        # Update user online status
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.id == user.id)
            )
            db_user = result.scalar_one_or_none()
            if db_user:
                db_user.is_online = True
                db_user.last_seen_at = datetime.utcnow()
                await session.commit()
        
        logger.info(f"User {user.id} connected with sid: {sid}")
        
        # Emit connection success
        await sio.emit("connected", {"user_id": str(user.id)}, room=sid)
        
        # Broadcast user status change to all users
        await sio.emit(
            "user_status_change",
            {
                "user_id": str(user.id),
                "is_online": True,
                "last_seen_at": datetime.utcnow().isoformat()
            },
            skip_sid=sid
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error in connect handler: {e}")
        await sio.disconnect(sid)
        return False


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    try:
        user_id = active_connections.get(sid)
        if user_id:
            # Update user offline status
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id == uuid.UUID(user_id))
                )
                db_user = result.scalar_one_or_none()
                if db_user:
                    db_user.is_online = False
                    db_user.last_seen_at = datetime.utcnow()
                    await session.commit()
            
            # Broadcast user status change to all users
            await sio.emit(
                "user_status_change",
                {
                    "user_id": user_id,
                    "is_online": False,
                    "last_seen_at": datetime.utcnow().isoformat()
                }
            )
            
            # Leave all rooms
            if user_id in user_rooms:
                for room_id in user_rooms[user_id]:
                    await sio.leave_room(sid, str(room_id))
                del user_rooms[user_id]
            
            del active_connections[sid]
            logger.info(f"User {user_id} disconnected: {sid}")
            
    except Exception as e:
        logger.error(f"Error in disconnect handler: {e}")


@sio.event
async def join_room(sid, data):
    """Handle user joining a chat room."""
    try:
        user_id = active_connections.get(sid)
        if not user_id:
            await sio.emit("error", {"message": "Not authenticated"}, room=sid)
            return
        
        room_id = data.get("room_id")
        if not room_id:
            await sio.emit("error", {"message": "room_id is required"}, room=sid)
            return
        
        # Join the Socket.IO room
        await sio.enter_room(sid, str(room_id))
        
        # Track user's rooms
        if user_id not in user_rooms:
            user_rooms[user_id] = set()
        user_rooms[user_id].add(str(room_id))
        
        logger.info(f"User {user_id} joined room {room_id}")
        
        # Notify user
        await sio.emit("room_joined", {"room_id": str(room_id)}, room=sid)
        
        # Notify other room members
        await sio.emit(
            "user_joined",
            {"room_id": str(room_id), "user_id": user_id},
            room=str(room_id),
            skip_sid=sid
        )
        
    except Exception as e:
        logger.error(f"Error in join_room handler: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def leave_room(sid, data):
    """Handle user leaving a chat room."""
    try:
        user_id = active_connections.get(sid)
        if not user_id:
            await sio.emit("error", {"message": "Not authenticated"}, room=sid)
            return
        
        room_id = data.get("room_id")
        if not room_id:
            await sio.emit("error", {"message": "room_id is required"}, room=sid)
            return
        
        # Leave the Socket.IO room
        await sio.leave_room(sid, str(room_id))
        
        # Update user's rooms
        if user_id in user_rooms:
            user_rooms[user_id].discard(str(room_id))
        
        logger.info(f"User {user_id} left room {room_id}")
        
        # Notify user
        await sio.emit("room_left", {"room_id": str(room_id)}, room=sid)
        
        # Notify other room members
        await sio.emit(
            "user_left",
            {"room_id": str(room_id), "user_id": user_id},
            room=str(room_id),
            skip_sid=sid
        )
        
    except Exception as e:
        logger.error(f"Error in leave_room handler: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def send_message(sid, data):
    """
    Handle sending a message.
    Note: This is a real-time notification. The actual message
    should be created via the REST API first.
    """
    try:
        user_id = active_connections.get(sid)
        if not user_id:
            await sio.emit("error", {"message": "Not authenticated"}, room=sid)
            return
        
        room_id = data.get("room_id")
        message_data = data.get("message")
        topic_id = data.get("topic_id")
        
        if not room_id or not message_data:
            await sio.emit("error", {"message": "room_id and message are required"}, room=sid)
            return
        
        # If this is a topic message, increment unread count for offline/inactive members
        if topic_id:
            async with AsyncSessionLocal() as session:
                # Get topic info
                topic_result = await session.execute(
                    select(Topic).where(Topic.id == uuid.UUID(topic_id))
                )
                topic = topic_result.scalar_one_or_none()
                
                # Get sender info
                sender_result = await session.execute(
                    select(User).where(User.id == uuid.UUID(user_id))
                )
                sender = sender_result.scalar_one_or_none()
                sender_name = sender.full_name or sender.email if sender else "Someone"
                
                # Get all topic members
                result = await session.execute(
                    select(TopicMember).where(TopicMember.topic_id == uuid.UUID(topic_id))
                )
                topic_members = result.scalars().all()
                
                offline_user_ids = []
                
                for member in topic_members:
                    # Skip the sender
                    if str(member.user_id) == user_id:
                        continue
                    
                    # Check if user is online and in the topic room
                    is_active_in_room = False
                    if str(member.user_id) in user_rooms:
                        if str(topic_id) in user_rooms[str(member.user_id)]:
                            is_active_in_room = True
                    
                    # Increment unread count if user is not active in the room
                    if not is_active_in_room:
                        member.unread_count += 1
                        offline_user_ids.append(member.user_id)
                
                await session.commit()
                
                # Send push notifications to offline users
                if offline_user_ids and topic:
                    for offline_user_id in offline_user_ids:
                        # Get push subscriptions for offline user
                        subs_result = await session.execute(
                            select(PushSubscription).where(
                                PushSubscription.user_id == offline_user_id
                            )
                        )
                        subscriptions = subs_result.scalars().all()
                        
                        # Send notification to each subscription
                        message_preview = message_data.get("content", "")[:100] if isinstance(message_data, dict) else str(message_data)[:100]
                        
                        for subscription in subscriptions:
                            # Pass FCM token directly
                            await notification_service.send_message_notification(
                                subscription_info=subscription.endpoint,
                                sender_name=sender_name,
                                message_preview=message_preview,
                                topic_name=topic.name,
                                topic_id=str(topic_id)
                            )
        
        # Broadcast message to room (for users currently in the topic)
        await sio.emit(
            "new_message",
            {
                "room_id": str(room_id),
                "message": message_data
            },
            room=str(room_id)
        )
        
        # Emit new_topic_message to topic room for consistency
        if topic_id:
            await sio.emit(
                "new_topic_message",
                {
                    "topic_id": str(topic_id),
                    "message": message_data
                },
                room=str(room_id)
            )
        
        # Broadcast global alert to all topic members' personal rooms
        if topic_id:
            async with AsyncSessionLocal() as session:
                # Get sender info for the alert
                sender_result = await session.execute(
                    select(User).where(User.id == uuid.UUID(user_id))
                )
                sender = sender_result.scalar_one_or_none()
                sender_name = sender.full_name or sender.email if sender else "Someone"
                
                # Get all topic members
                result = await session.execute(
                    select(TopicMember).where(TopicMember.topic_id == uuid.UUID(topic_id))
                )
                topic_members = result.scalars().all()
                
                # Emit global alert to each member's personal room
                message_preview = message_data.get("content", "")[:100] if isinstance(message_data, dict) else str(message_data)[:100]
                
                for member in topic_members:
                    # Skip the sender
                    if str(member.user_id) == user_id:
                        continue
                    
                    # Emit to user's personal room
                    member_room = f"user_{member.user_id}"
                    await sio.emit(
                        "global_message_alert",
                        {
                            "topic_id": str(topic_id),
                            "message_preview": message_preview,
                            "sender_name": sender_name
                        },
                        room=member_room
                    )
        
        logger.info(f"Message sent to room {room_id} by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in send_message handler: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def typing(sid, data):
    """Handle typing indicator."""
    try:
        user_id = active_connections.get(sid)
        if not user_id:
            return
        
        room_id = data.get("room_id")
        is_typing = data.get("is_typing", False)
        
        if not room_id:
            return
        
        # Broadcast typing status to room (excluding sender)
        await sio.emit(
            "user_typing",
            {
                "room_id": str(room_id),
                "user_id": user_id,
                "is_typing": is_typing
            },
            room=str(room_id),
            skip_sid=sid
        )
        
    except Exception as e:
        logger.error(f"Error in typing handler: {e}")


@sio.event
async def message_edited(sid, data):
    """Broadcast message edit notification."""
    try:
        user_id = active_connections.get(sid)
        if not user_id:
            return
        
        room_id = data.get("room_id")
        message_id = data.get("message_id")
        content = data.get("content")
        
        if not all([room_id, message_id, content]):
            return
        
        # Broadcast edit to room
        await sio.emit(
            "message_edited",
            {
                "room_id": str(room_id),
                "message_id": str(message_id),
                "content": content,
                "edited_by": user_id
            },
            room=str(room_id)
        )
        
    except Exception as e:
        logger.error(f"Error in message_edited handler: {e}")


@sio.event
async def message_deleted(sid, data):
    """Broadcast message deletion notification."""
    try:
        user_id = active_connections.get(sid)
        if not user_id:
            return
        
        room_id = data.get("room_id")
        message_id = data.get("message_id")
        
        if not all([room_id, message_id]):
            return
        
        # Broadcast deletion to room
        await sio.emit(
            "message_deleted",
            {
                "room_id": str(room_id),
                "message_id": str(message_id),
                "deleted_by": user_id
            },
            room=str(room_id)
        )
        
    except Exception as e:
        logger.error(f"Error in message_deleted handler: {e}")


@sio.event
async def mark_as_read(sid, data):
    """Handle marking messages as read."""
    try:
        user_id = active_connections.get(sid)
        if not user_id:
            return
        
        room_id = data.get("room_id")
        topic_id = data.get("topic_id")
        message_ids = data.get("message_ids", [])
        
        if not room_id:
            return
        
        # Reset unread count for topic member
        if topic_id:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(TopicMember).where(
                        TopicMember.topic_id == uuid.UUID(topic_id),
                        TopicMember.user_id == uuid.UUID(user_id)
                    )
                )
                topic_member = result.scalar_one_or_none()
                if topic_member:
                    topic_member.unread_count = 0
                    topic_member.last_read_at = datetime.utcnow()
                    await session.commit()
        
        # Broadcast read receipt to room
        await sio.emit(
            "messages_read",
            {
                "room_id": str(room_id),
                "user_id": user_id,
                "message_ids": message_ids
            },
            room=str(room_id),
            skip_sid=sid
        )
        
    except Exception as e:
        logger.error(f"Error in mark_as_read handler: {e}")


# Helper function to emit to specific user
async def emit_to_user(user_id: str, event: str, data: dict):
    """
    Emit an event to a specific user across all their connections.
    
    Args:
        user_id: User ID to send to
        event: Event name
        data: Event data
    """
    try:
        # Find all sessions for this user
        for sid, uid in active_connections.items():
            if uid == user_id:
                await sio.emit(event, data, room=sid)
    except Exception as e:
        logger.error(f"Error emitting to user {user_id}: {e}")


# Helper function to emit to room
async def emit_to_room(room_id: str, event: str, data: dict, exclude_user: Optional[str] = None):
    """
    Emit an event to all users in a room.
    
    Args:
        room_id: Room ID to send to
        event: Event name
        data: Event data
        exclude_user: Optional user ID to exclude
    """
    try:
        if exclude_user:
            # Find sid to skip
            skip_sid = None
            for sid, uid in active_connections.items():
                if uid == exclude_user:
                    skip_sid = sid
                    break
            
            await sio.emit(event, data, room=str(room_id), skip_sid=skip_sid)
        else:
            await sio.emit(event, data, room=str(room_id))
    except Exception as e:
        logger.error(f"Error emitting to room {room_id}: {e}")


# ============================================================================
# Topic/Channel Socket.IO Events
# ============================================================================

@sio.event
async def join_topic(sid, data):
    """Handle user joining a topic."""
    try:
        user_id = active_connections.get(sid)
        if not user_id:
            await sio.emit("error", {"message": "Not authenticated"}, room=sid)
            return
        
        topic_id = data.get("topic_id")
        if not topic_id:
            await sio.emit("error", {"message": "topic_id is required"}, room=sid)
            return
        
        # Join the Socket.IO room
        await sio.enter_room(sid, str(topic_id))
        
        # Track user's rooms
        if user_id not in user_rooms:
            user_rooms[user_id] = set()
        user_rooms[user_id].add(str(topic_id))
        
        logger.info(f"User {user_id} joined topic {topic_id}")
        
        # Notify user
        await sio.emit("topic_joined", {"topic_id": str(topic_id)}, room=sid)
        
        # Notify other topic members
        await sio.emit(
            "user_joined_topic",
            {"topic_id": str(topic_id), "user_id": user_id},
            room=str(topic_id),
            skip_sid=sid
        )
        
    except Exception as e:
        logger.error(f"Error in join_topic handler: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def leave_topic(sid, data):
    """Handle user leaving a topic."""
    try:
        user_id = active_connections.get(sid)
        if not user_id:
            await sio.emit("error", {"message": "Not authenticated"}, room=sid)
            return
        
        topic_id = data.get("topic_id")
        if not topic_id:
            await sio.emit("error", {"message": "topic_id is required"}, room=sid)
            return
        
        # Leave the Socket.IO room
        await sio.leave_room(sid, str(topic_id))
        
        # Update user's rooms
        if user_id in user_rooms:
            user_rooms[user_id].discard(str(topic_id))
        
        logger.info(f"User {user_id} left topic {topic_id}")
        
        # Notify user
        await sio.emit("topic_left", {"topic_id": str(topic_id)}, room=sid)
        
        # Notify other topic members
        await sio.emit(
            "user_left_topic",
            {"topic_id": str(topic_id), "user_id": user_id},
            room=str(topic_id),
            skip_sid=sid
        )
        
    except Exception as e:
        logger.error(f"Error in leave_topic handler: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)


@sio.event
async def topic_typing(sid, data):
    """Handle typing indicator in topics."""
    try:
        user_id = active_connections.get(sid)
        if not user_id:
            return
        
        topic_id = data.get("topic_id")
        is_typing = data.get("is_typing", False)
        
        if not topic_id:
            return
        
        # Broadcast typing status to topic (excluding sender)
        await sio.emit(
            "user_typing_topic",
            {
                "topic_id": str(topic_id),
                "user_id": user_id,
                "is_typing": is_typing
            },
            room=str(topic_id),
            skip_sid=sid
        )
        
    except Exception as e:
        logger.error(f"Error in topic_typing handler: {e}")


@sio.event
async def mention_notification(sid, data):
    """Handle mention notifications."""
    try:
        user_id = active_connections.get(sid)
        if not user_id:
            return
        
        mentioned_user_id = data.get("mentioned_user_id")
        topic_id = data.get("topic_id")
        message_id = data.get("message_id")
        
        if not all([mentioned_user_id, topic_id, message_id]):
            return
        
        # Emit mention notification to mentioned user
        await emit_to_user(
            mentioned_user_id,
            "mentioned",
            {
                "topic_id": str(topic_id),
                "message_id": str(message_id),
                "mentioned_by": user_id
            }
        )
        
    except Exception as e:
        logger.error(f"Error in mention_notification handler: {e}")
