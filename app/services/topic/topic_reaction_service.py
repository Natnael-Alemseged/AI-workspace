"""Topic message reaction service."""
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.channel import MessageReaction


class TopicReactionService:
    """Service for message reaction operations."""
    
    @staticmethod
    async def add_reaction(
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> MessageReaction:
        """Add a reaction to a message."""
        try:
            # Check if reaction already exists for this user and message
            existing_query = select(MessageReaction).where(
                and_(
                    MessageReaction.message_id == message_id,
                    MessageReaction.user_id == user_id
                )
            )
            existing_result = await session.execute(existing_query)
            existing_reaction = existing_result.scalar_one_or_none()
            
            if existing_reaction:
                # Update existing reaction
                if existing_reaction.emoji != emoji:
                    existing_reaction.emoji = emoji
                    await session.commit()
                    await session.refresh(existing_reaction)
                    logger.info(f"Reaction updated: {emoji} for message {message_id} by user {user_id}")
                return existing_reaction
            
            # Create reaction
            reaction = MessageReaction(
                message_id=message_id,
                user_id=user_id,
                emoji=emoji
            )
            session.add(reaction)
            await session.commit()
            await session.refresh(reaction)
            
            logger.info(f"Reaction added: {emoji} to message {message_id} by user {user_id}")
            return reaction
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error adding reaction: {e}")
            raise
    
    @staticmethod
    async def remove_reaction(
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> bool:
        """Remove a reaction from a message."""
        try:
            # Get reaction
            query = select(MessageReaction).where(
                and_(
                    MessageReaction.message_id == message_id,
                    MessageReaction.user_id == user_id,
                    MessageReaction.emoji == emoji
                )
            )
            result = await session.execute(query)
            reaction = result.scalar_one_or_none()
            
            if not reaction:
                return False
            
            # Delete reaction
            await session.delete(reaction)
            await session.commit()
            
            logger.info(f"Reaction removed: {emoji} from message {message_id} by user {user_id}")
            return True
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error removing reaction: {e}")
            raise
