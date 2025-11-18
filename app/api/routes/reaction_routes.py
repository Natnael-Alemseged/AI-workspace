"""Message reaction API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.users_complete import get_current_user
from app.core.logging import logger
from app.db import get_async_session
from app.models.channel import TopicMessage
from app.models.user import User
from app.schemas.channel import ReactionCreate
from app.services.socketio_service import emit_to_room
from app.services.topic import TopicService

router = APIRouter()


@router.post("/topics/messages/{message_id}/reactions", status_code=status.HTTP_201_CREATED)
async def add_reaction(
    message_id: UUID,
    reaction_data: ReactionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Add a reaction to a message."""
    try:
        reaction = await TopicService.add_reaction(
            session, message_id, current_user.id, reaction_data.emoji
        )
        
        # Get topic_id for notification
        query = select(TopicMessage).where(TopicMessage.id == message_id)
        result = await session.execute(query)
        message = result.scalar_one_or_none()
        
        if message:
            # Notify topic members
            await emit_to_room(
                str(message.topic_id),
                "reaction_added",
                {
                    "topic_id": str(message.topic_id),
                    "message_id": str(message_id),
                    "user_id": str(current_user.id),
                    "emoji": reaction_data.emoji
                }
            )
        
        return {"message": "Reaction added successfully"}
        
    except Exception as e:
        logger.error(f"Error adding reaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add reaction"
        )


@router.delete("/topics/messages/{message_id}/reactions/{emoji}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_reaction(
    message_id: UUID,
    emoji: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove a reaction from a message."""
    try:
        # Get topic_id for notification
        query = select(TopicMessage).where(TopicMessage.id == message_id)
        result = await session.execute(query)
        message = result.scalar_one_or_none()
        
        success = await TopicService.remove_reaction(
            session, message_id, current_user.id, emoji
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reaction not found"
            )
        
        if message:
            # Notify topic members
            await emit_to_room(
                str(message.topic_id),
                "reaction_removed",
                {
                    "topic_id": str(message.topic_id),
                    "message_id": str(message_id),
                    "user_id": str(current_user.id),
                    "emoji": emoji
                }
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing reaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove reaction"
        )
