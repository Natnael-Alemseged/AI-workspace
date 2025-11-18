"""Topic message API endpoints."""
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.users_complete import get_current_user
from app.core.logging import logger
from app.db import get_async_session
from app.models.channel import TopicMessage
from app.models.user import User
from app.schemas.channel import (
    MessageListResponse,
    TopicMessageCreate,
    TopicMessageRead,
    TopicMessageUpdate,
)
from app.core.ai_bots import get_bot_avatar, get_bot_id_for_agent_type, get_bot_name
from app.services.chat import agent_service
from app.services.socketio_service import emit_to_room
from app.services.topic import TopicService
from app.utils.ai_agent_parser import parse_agent_mention

router = APIRouter()


@router.post("/topics/{topic_id}/messages", response_model=TopicMessageRead, status_code=status.HTTP_201_CREATED)
async def create_topic_message(
    topic_id: UUID,
    message_data: TopicMessageCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create a new message in a topic. AI mentions are processed asynchronously."""
    try:
        message = await TopicService.create_message(
            session, topic_id, message_data, current_user.id
        )
        
        # Notify topic members via Socket.IO
        await emit_to_room(
            str(message.topic_id),
            "new_topic_message",
            {
                "topic_id": str(message.topic_id),
                "message": {
                    "id": str(message.id),
                    "sender_id": str(message.sender_id),
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                    "reply_to_id": str(message.reply_to_id) if message.reply_to_id else None,
                    "is_edited": False,
                    "is_deleted": False,
                    # Include sender info to match REST API response
                    "sender_email": message.sender.email if message.sender else None,
                    "sender_full_name": message.sender.full_name if message.sender else None,
                    "mention_count": 0,
                    "reaction_count": 0,
                    "reactions": []
                }
            }
        )
        
        # Check if message contains AI agent mention
        agent_mention = parse_agent_mention(message_data.content)
        if agent_mention:
            logger.info(f"Queueing AI agent {agent_mention.agent_type} for background processing")
            # Queue AI processing in background
            background_tasks.add_task(
                process_ai_topic_response,
                reply_to_message_id=message.id,
                topic_id=topic_id,
                user_id=current_user.id,
                prompt=agent_mention.prompt,
                agent_type=agent_mention.agent_type.value,
                user_name=current_user.full_name or current_user.email
            )
        
        return message
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create message"
        )


@router.get("/topics/{topic_id}/messages", response_model=MessageListResponse)
async def get_topic_messages(
    topic_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get messages for a topic."""
    try:
        messages, total = await TopicService.get_topic_messages(
            session, topic_id, current_user.id, page, page_size
        )
        
        has_more = (page * page_size) < total
        
        return MessageListResponse(
            messages=messages,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )


@router.patch("/topics/messages/{message_id}", response_model=TopicMessageRead)
async def update_topic_message(
    message_id: UUID,
    message_data: TopicMessageUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update (edit) a message."""
    try:
        message = await TopicService.update_message(
            session, message_id, current_user.id, message_data.content
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Notify topic members
        await emit_to_room(
            str(message.topic_id),
            "topic_message_edited",
            {
                "topic_id": str(message.topic_id),
                "message_id": str(message_id),
                "content": message.content,
                "edited_by": str(current_user.id)
            }
        )
        
        return message
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message"
        )


@router.delete("/topics/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a message."""
    try:
        # Get message first to get topic_id
        query = select(TopicMessage).where(TopicMessage.id == message_id)
        result = await session.execute(query)
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        topic_id = message.topic_id
        
        success = await TopicService.delete_message(
            session, message_id, current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Notify topic members
        await emit_to_room(
            str(topic_id),
            "topic_message_deleted",
            {
                "topic_id": str(topic_id),
                "message_id": str(message_id),
                "deleted_by": str(current_user.id)
            }
        )
        
        return None
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        )


async def process_ai_topic_response(
    reply_to_message_id: UUID,
    topic_id: UUID,
    user_id: UUID,
    prompt: str,
    agent_type: str,
    user_name: str
):
    """
    Process AI response in background and send as a reply to the original message.
    
    Args:
        reply_to_message_id: The message ID to reply to
        topic_id: Topic ID
        user_id: User ID who sent the message
        prompt: The prompt for the AI agent
        agent_type: Type of AI agent (emailAi, searchAi, etc.)
        user_name: User's display name
    """
    from app.db import async_session_maker
    from app.services.topic.topic_message_service import TopicMessageService
    
    try:
        # Show "AI is typing" indicator
        await emit_to_room(
            str(topic_id),
            "typing",
            {
                "topic_id": str(topic_id),
                "user_type": "ai",
                "is_typing": True
            }
        )
        
        logger.info(f"Processing AI {agent_type} for message {reply_to_message_id}")
        
        # Process with AI (can take time)
        ai_response = await agent_service.run_agent_stream(
            prompt=prompt,
            user_id=str(user_id),
            agent_type=agent_type
        )
        
        # Create new session for background task
        async with async_session_maker() as session:
            # Create AI response as a REPLY to the user's message
            ai_message = await TopicMessageService.create_ai_message(
                session,
                topic_id=topic_id,
                content=ai_response,
                reply_to_id=reply_to_message_id,
                agent_type=agent_type
            )
            
            # Get bot info
            bot_id = get_bot_id_for_agent_type(agent_type)
            bot_name = get_bot_name(bot_id)
            bot_avatar = get_bot_avatar(bot_id)
            
            # Stop typing indicator
            await emit_to_room(
                str(topic_id),
                "typing",
                {
                    "topic_id": str(topic_id),
                    "user_type": "ai",
                    "is_typing": False
                }
            )
            
            # Emit AI response with reply context
            await emit_to_room(
                str(topic_id),
                "new_topic_message",
                {
                    "topic_id": str(topic_id),
                    "message": {
                        "id": str(ai_message.id),
                        "sender_id": str(bot_id),
                        "content": ai_message.content,
                        "created_at": ai_message.created_at.isoformat(),
                        "reply_to_id": str(reply_to_message_id),
                        "reply_to": {
                            "id": str(reply_to_message_id),
                            "content": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                            "sender_name": user_name
                        },
                        "is_edited": False,
                        "is_deleted": False,
                        # Include sender info to match REST API response
                        "sender_email": f"{agent_type.lower()}@armada.bot",
                        "sender_full_name": bot_name,
                        "mention_count": 0,
                        "reaction_count": 0,
                        "reactions": []
                    }
                }
            )
            
            logger.info(f"AI {agent_type} replied to message {reply_to_message_id}")
            
    except Exception as e:
        logger.error(f"Error processing AI topic response: {e}", exc_info=True)
        
        # Emit error to topic
        try:
            await emit_to_room(
                str(topic_id),
                "typing",
                {
                    "topic_id": str(topic_id),
                    "user_type": "ai",
                    "is_typing": False
                }
            )
            
            await emit_to_room(
                str(topic_id),
                "ai_error",
                {
                    "topic_id": str(topic_id),
                    "error": f"AI {agent_type} failed to process your request",
                    "original_message_id": str(reply_to_message_id)
                }
            )
        except Exception as emit_error:
            logger.error(f"Error emitting AI error: {emit_error}")
