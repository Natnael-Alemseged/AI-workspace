"""Chat service for business logic."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.ai_bots import EMAIL_AI_BOT_ID, GENERAL_AI_BOT_ID, SEARCH_AI_BOT_ID, get_bot_id_for_agent_type
from app.core.logging import logger
from app.models.chat import (
    ChatMessage,
    ChatRoom,
    ChatRoomMember,
    ChatRoomType,
    MessageReadReceipt,
    MessageType,
)
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatRoomCreate,
    ChatRoomRead,
    ChatRoomUpdate,
)


class ChatService:
    """Service for chat operations."""
    
    @staticmethod
    async def create_room(
        session: AsyncSession,
        room_data: ChatRoomCreate,
        creator_id: UUID
    ) -> ChatRoom:
        """
        Create a new chat room.
        
        Args:
            session: Database session
            room_data: Room creation data
            creator_id: ID of the user creating the room
            
        Returns:
            Created ChatRoom
        """
        try:
            # For direct chats, check if room already exists
            if room_data.room_type == ChatRoomType.DIRECT:
                if len(room_data.member_ids) != 1:
                    raise ValueError("Direct chat must have exactly 1 other member")
                
                # Check for existing direct chat
                other_user_id = room_data.member_ids[0]
                existing_room = await ChatService._find_direct_chat(
                    session, creator_id, other_user_id
                )
                if existing_room:
                    return existing_room
            
            # Create room
            room = ChatRoom(
                name=room_data.name,
                room_type=room_data.room_type,
                description=room_data.description,
                created_by=creator_id,
                is_active=True
            )
            session.add(room)
            await session.flush()
            
            # Add creator as member and admin
            creator_member = ChatRoomMember(
                room_id=room.id,
                user_id=creator_id,
                is_admin=True,
                is_active=True
            )
            session.add(creator_member)
            
            # Add other members
            for member_id in room_data.member_ids:
                member = ChatRoomMember(
                    room_id=room.id,
                    user_id=member_id,
                    is_admin=False,
                    is_active=True
                )
                session.add(member)
            
            # Automatically add AI bots to group chats (not direct chats)
            if room_data.room_type == ChatRoomType.GROUP:
                bot_ids = [EMAIL_AI_BOT_ID, SEARCH_AI_BOT_ID, GENERAL_AI_BOT_ID]
                for bot_id in bot_ids:
                    bot_member = ChatRoomMember(
                        room_id=room.id,
                        user_id=bot_id,
                        is_admin=False,
                        is_active=True
                    )
                    session.add(bot_member)
                logger.info(f"Added 3 AI bots to group chat room {room.id}")
            
            await session.commit()
            
            # Reload room with members eagerly loaded
            query = select(ChatRoom).where(ChatRoom.id == room.id).options(
                selectinload(ChatRoom.members).selectinload(ChatRoomMember.user)
            )
            result = await session.execute(query)
            room = result.scalar_one()
            
            logger.info(f"Chat room created: {room.id}")
            return room
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating chat room: {e}")
            raise
    
    @staticmethod
    async def _find_direct_chat(
        session: AsyncSession,
        user1_id: UUID,
        user2_id: UUID
    ) -> Optional[ChatRoom]:
        """Find existing direct chat between two users."""
        query = (
            select(ChatRoom)
            .join(ChatRoomMember, ChatRoom.id == ChatRoomMember.room_id)
            .where(
                and_(
                    ChatRoom.room_type == ChatRoomType.DIRECT,
                    ChatRoom.is_active == True,
                    ChatRoomMember.user_id.in_([user1_id, user2_id])
                )
            )
            .group_by(ChatRoom.id)
            .having(func.count(ChatRoomMember.id) == 2)
            .options(
                selectinload(ChatRoom.members).selectinload(ChatRoomMember.user)
            )
        )
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_rooms(
        session: AsyncSession,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[ChatRoom], int]:
        """
        Get all chat rooms for a user.
        
        Args:
            session: Database session
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            Tuple of (rooms list, total count)
        """
        try:
            # Count total
            count_query = (
                select(func.count(ChatRoom.id))
                .join(ChatRoomMember, ChatRoom.id == ChatRoomMember.room_id)
                .where(
                    and_(
                        ChatRoomMember.user_id == user_id,
                        ChatRoomMember.is_active == True,
                        ChatRoom.is_active == True
                    )
                )
            )
            total_result = await session.execute(count_query)
            total = total_result.scalar_one()
            
            # Get rooms
            offset = (page - 1) * page_size
            query = (
                select(ChatRoom)
                .join(ChatRoomMember, ChatRoom.id == ChatRoomMember.room_id)
                .where(
                    and_(
                        ChatRoomMember.user_id == user_id,
                        ChatRoomMember.is_active == True,
                        ChatRoom.is_active == True
                    )
                )
                .order_by(ChatRoom.updated_at.desc())
                .offset(offset)
                .limit(page_size)
                .options(selectinload(ChatRoom.members))
            )
            
            result = await session.execute(query)
            rooms = result.scalars().unique().all()
            
            return list(rooms), total
            
        except Exception as e:
            logger.error(f"Error getting user rooms: {e}")
            raise
    
    @staticmethod
    async def get_room_by_id(
        session: AsyncSession,
        room_id: UUID,
        user_id: UUID
    ) -> Optional[ChatRoom]:
        """Get room by ID if user is a member."""
        try:
            query = (
                select(ChatRoom)
                .join(ChatRoomMember, ChatRoom.id == ChatRoomMember.room_id)
                .where(
                    and_(
                        ChatRoom.id == room_id,
                        ChatRoomMember.user_id == user_id,
                        ChatRoomMember.is_active == True,
                        ChatRoom.is_active == True
                    )
                )
                .options(
                    selectinload(ChatRoom.members).selectinload(ChatRoomMember.user)
                )
            )
            
            result = await session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting room: {e}")
            raise
    
    @staticmethod
    async def update_room(
        session: AsyncSession,
        room_id: UUID,
        user_id: UUID,
        room_data: ChatRoomUpdate
    ) -> Optional[ChatRoom]:
        """Update room (only admins can update)."""
        try:
            # Check if user is admin
            member_query = select(ChatRoomMember).where(
                and_(
                    ChatRoomMember.room_id == room_id,
                    ChatRoomMember.user_id == user_id,
                    ChatRoomMember.is_admin == True,
                    ChatRoomMember.is_active == True
                )
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()
            
            if not member:
                raise ValueError("User is not an admin of this room")
            
            # Get room
            room_query = select(ChatRoom).where(ChatRoom.id == room_id)
            room_result = await session.execute(room_query)
            room = room_result.scalar_one_or_none()
            
            if not room:
                return None
            
            # Update fields
            if room_data.name is not None:
                room.name = room_data.name
            if room_data.description is not None:
                room.description = room_data.description
            if room_data.avatar_url is not None:
                room.avatar_url = room_data.avatar_url
            
            room.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(room)
            
            logger.info(f"Room updated: {room_id}")
            return room
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating room: {e}")
            raise
    
    @staticmethod
    async def add_member(
        session: AsyncSession,
        room_id: UUID,
        user_id: UUID,
        new_member_id: UUID
    ) -> ChatRoomMember:
        """Add a member to a room (only admins can add)."""
        try:
            # Check if user is admin
            admin_query = select(ChatRoomMember).where(
                and_(
                    ChatRoomMember.room_id == room_id,
                    ChatRoomMember.user_id == user_id,
                    ChatRoomMember.is_admin == True,
                    ChatRoomMember.is_active == True
                )
            )
            admin_result = await session.execute(admin_query)
            admin = admin_result.scalar_one_or_none()
            
            if not admin:
                raise ValueError("User is not an admin of this room")
            
            # Check if member already exists
            existing_query = select(ChatRoomMember).where(
                and_(
                    ChatRoomMember.room_id == room_id,
                    ChatRoomMember.user_id == new_member_id
                )
            )
            existing_result = await session.execute(existing_query)
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                if existing.is_active:
                    raise ValueError("User is already a member")
                # Reactivate
                existing.is_active = True
                await session.commit()
                return existing
            
            # Add new member
            member = ChatRoomMember(
                room_id=room_id,
                user_id=new_member_id,
                is_admin=False,
                is_active=True
            )
            session.add(member)
            await session.commit()
            await session.refresh(member)
            
            logger.info(f"Member {new_member_id} added to room {room_id}")
            return member
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error adding member: {e}")
            raise
    
    @staticmethod
    async def remove_member(
        session: AsyncSession,
        room_id: UUID,
        user_id: UUID,
        member_id: UUID
    ) -> bool:
        """Remove a member from a room (admins or self)."""
        try:
            # Check if user is admin or removing themselves
            if user_id != member_id:
                admin_query = select(ChatRoomMember).where(
                    and_(
                        ChatRoomMember.room_id == room_id,
                        ChatRoomMember.user_id == user_id,
                        ChatRoomMember.is_admin == True,
                        ChatRoomMember.is_active == True
                    )
                )
                admin_result = await session.execute(admin_query)
                admin = admin_result.scalar_one_or_none()
                
                if not admin:
                    raise ValueError("User is not authorized to remove members")
            
            # Soft delete member
            member_query = select(ChatRoomMember).where(
                and_(
                    ChatRoomMember.room_id == room_id,
                    ChatRoomMember.user_id == member_id
                )
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()
            
            if not member:
                return False
            
            member.is_active = False
            await session.commit()
            
            logger.info(f"Member {member_id} removed from room {room_id}")
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error removing member: {e}")
            raise
    
    @staticmethod
    async def create_message(
        session: AsyncSession,
        message_data: ChatMessageCreate,
        sender_id: UUID
    ) -> ChatMessage:
        """Create a new message."""
        try:
            # Verify user is member of room
            member_query = select(ChatRoomMember).where(
                and_(
                    ChatRoomMember.room_id == message_data.room_id,
                    ChatRoomMember.user_id == sender_id,
                    ChatRoomMember.is_active == True
                )
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()
            
            if not member:
                raise ValueError("User is not a member of this room")
            
            # Create message
            message = ChatMessage(
                room_id=message_data.room_id,
                sender_id=sender_id,
                message_type=message_data.message_type,
                content=message_data.content,
                reply_to_id=message_data.reply_to_id,
                forwarded_from_id=message_data.forwarded_from_id,
                is_edited=False,
                is_deleted=False
            )
            session.add(message)
            
            # Update room's updated_at
            room_query = select(ChatRoom).where(ChatRoom.id == message_data.room_id)
            room_result = await session.execute(room_query)
            room = room_result.scalar_one_or_none()
            if room:
                room.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(message)
            
            logger.info(f"Message created: {message.id} in room {message_data.room_id}")
            return message
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating message: {e}")
            raise
    
    @staticmethod
    async def create_ai_message(
        session: AsyncSession,
        message_data: ChatMessageCreate,
        agent_type: str = "emailAi"
    ) -> ChatMessage:
        """Create a message from AI bot using the bot user ID."""
        try:
            # Get the bot user ID for this agent type
            bot_id = get_bot_id_for_agent_type(agent_type)
            
            # Create message with bot user as sender
            message = ChatMessage(
                room_id=message_data.room_id,
                sender_id=bot_id,
                message_type=message_data.message_type,
                content=message_data.content,
                reply_to_id=message_data.reply_to_id,
                forwarded_from_id=message_data.forwarded_from_id,
                is_edited=False,
                is_deleted=False
            )
            session.add(message)
            
            # Update room's updated_at
            room_query = select(ChatRoom).where(ChatRoom.id == message_data.room_id)
            room_result = await session.execute(room_query)
            room = room_result.scalar_one_or_none()
            if room:
                room.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(message)
            
            logger.info(f"AI message created: {message.id} in room {message_data.room_id}")
            return message
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating AI message: {e}")
            raise
    
    @staticmethod
    async def get_room_messages(
        session: AsyncSession,
        room_id: UUID,
        user_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list[ChatMessage], int]:
        """Get messages for a room."""
        try:
            # Verify user is member
            member_query = select(ChatRoomMember).where(
                and_(
                    ChatRoomMember.room_id == room_id,
                    ChatRoomMember.user_id == user_id,
                    ChatRoomMember.is_active == True
                )
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()
            
            if not member:
                raise ValueError("User is not a member of this room")
            
            # Count total
            count_query = (
                select(func.count(ChatMessage.id))
                .where(
                    and_(
                        ChatMessage.room_id == room_id,
                        ChatMessage.is_deleted == False
                    )
                )
            )
            total_result = await session.execute(count_query)
            total = total_result.scalar_one()
            
            # Get messages
            offset = (page - 1) * page_size
            query = (
                select(ChatMessage)
                .where(
                    and_(
                        ChatMessage.room_id == room_id,
                        ChatMessage.is_deleted == False
                    )
                )
                .order_by(ChatMessage.created_at.desc())
                .offset(offset)
                .limit(page_size)
                .options(
                    joinedload(ChatMessage.sender),
                    joinedload(ChatMessage.reply_to),
                    selectinload(ChatMessage.read_receipts)
                )
            )
            
            result = await session.execute(query)
            messages = result.scalars().unique().all()
            
            return list(messages), total
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            raise
    
    @staticmethod
    async def update_message(
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID,
        content: str
    ) -> Optional[ChatMessage]:
        """Update (edit) a message."""
        try:
            # Get message
            query = select(ChatMessage).where(ChatMessage.id == message_id)
            result = await session.execute(query)
            message = result.scalar_one_or_none()
            
            if not message:
                return None
            
            # Check if user is sender
            if message.sender_id != user_id:
                raise ValueError("User is not the sender of this message")
            
            # Update message
            message.content = content
            message.is_edited = True
            message.edited_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(message)
            
            logger.info(f"Message edited: {message_id}")
            return message
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating message: {e}")
            raise
    
    @staticmethod
    async def delete_message(
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a message (soft delete)."""
        try:
            # Get message
            query = select(ChatMessage).where(ChatMessage.id == message_id)
            result = await session.execute(query)
            message = result.scalar_one_or_none()
            
            if not message:
                return False
            
            # Check if user is sender or room admin
            if message.sender_id != user_id:
                # Check if user is admin
                admin_query = select(ChatRoomMember).where(
                    and_(
                        ChatRoomMember.room_id == message.room_id,
                        ChatRoomMember.user_id == user_id,
                        ChatRoomMember.is_admin == True,
                        ChatRoomMember.is_active == True
                    )
                )
                admin_result = await session.execute(admin_query)
                admin = admin_result.scalar_one_or_none()
                
                if not admin:
                    raise ValueError("User is not authorized to delete this message")
            
            # Soft delete
            message.is_deleted = True
            message.deleted_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(f"Message deleted: {message_id}")
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting message: {e}")
            raise
    
    @staticmethod
    async def mark_messages_as_read(
        session: AsyncSession,
        room_id: UUID,
        user_id: UUID,
        message_ids: list[UUID]
    ) -> list[MessageReadReceipt]:
        """Mark messages as read."""
        try:
            receipts = []
            
            for message_id in message_ids:
                # Check if receipt already exists
                existing_query = select(MessageReadReceipt).where(
                    and_(
                        MessageReadReceipt.message_id == message_id,
                        MessageReadReceipt.user_id == user_id
                    )
                )
                existing_result = await session.execute(existing_query)
                existing = existing_result.scalar_one_or_none()
                
                if not existing:
                    receipt = MessageReadReceipt(
                        message_id=message_id,
                        user_id=user_id
                    )
                    session.add(receipt)
                    receipts.append(receipt)
            
            # Update last_read_at for member
            member_query = select(ChatRoomMember).where(
                and_(
                    ChatRoomMember.room_id == room_id,
                    ChatRoomMember.user_id == user_id
                )
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()
            
            if member:
                member.last_read_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(f"Marked {len(receipts)} messages as read for user {user_id}")
            return receipts
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error marking messages as read: {e}")
            raise
