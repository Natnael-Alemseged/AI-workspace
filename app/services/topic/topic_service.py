"""Topic service - Main service delegating to specialized sub-services."""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import MessageReaction, Topic, TopicMember, TopicMessage
from app.schemas.channel import ReactionSummary, TopicCreate, TopicMessageCreate, TopicUpdate
from app.services.topic.topic_management_service import TopicManagementService
from app.services.topic.topic_member_service import TopicMemberService
from app.services.topic.topic_message_service import TopicMessageService
from app.services.topic.topic_reaction_service import TopicReactionService


class TopicService:
    """
    Main service for topic operations.
    Delegates to specialized sub-services for better organization.
    """
    
    # ============================================================================
    # Topic Management Operations
    # ============================================================================
    
    @staticmethod
    async def verify_admin(session: AsyncSession, user_id: UUID) -> bool:
        """Verify if user is an admin."""
        return await TopicManagementService.verify_admin(session, user_id)
    
    @staticmethod
    async def create_topic(
        session: AsyncSession,
        topic_data: TopicCreate,
        creator_id: UUID
    ) -> Topic:
        """Create a new topic (admin only)."""
        return await TopicManagementService.create_topic(session, topic_data, creator_id)
    
    @staticmethod
    async def get_channel_topics(
        session: AsyncSession,
        channel_id: UUID,
        page: int = 1,
        page_size: int = 50,
        user_id: Optional[UUID] = None
    ) -> tuple[list[Topic], int]:
        """Get topics in a channel that the user is a member of."""
        return await TopicManagementService.get_channel_topics(session, channel_id, page, page_size, user_id)
    
    @staticmethod
    async def get_user_topics(
        session: AsyncSession,
        user_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list[Topic], int]:
        """Get all topics a user is a member of."""
        return await TopicManagementService.get_user_topics(session, user_id, page, page_size)
    
    @staticmethod
    async def get_topic_by_id(
        session: AsyncSession,
        topic_id: UUID,
        user_id: UUID
    ) -> Optional[Topic]:
        """Get topic by ID if user is a member."""
        return await TopicManagementService.get_topic_by_id(session, topic_id, user_id)
    
    @staticmethod
    async def update_topic(
        session: AsyncSession,
        topic_id: UUID,
        user_id: UUID,
        topic_data: TopicUpdate
    ) -> Optional[Topic]:
        """Update topic (admin only)."""
        return await TopicManagementService.update_topic(session, topic_id, user_id, topic_data)
    
    # ============================================================================
    # Topic Member Operations
    # ============================================================================
    
    @staticmethod
    async def add_member(
        session: AsyncSession,
        topic_id: UUID,
        admin_id: UUID,
        user_id: UUID
    ) -> TopicMember:
        """Add a member to a topic (admin only)."""
        return await TopicMemberService.add_member(session, topic_id, admin_id, user_id)
    
    @staticmethod
    async def remove_member(
        session: AsyncSession,
        topic_id: UUID,
        admin_id: UUID,
        user_id: UUID
    ) -> bool:
        """Remove a member from a topic (admin only)."""
        return await TopicMemberService.remove_member(session, topic_id, admin_id, user_id)
    
    @staticmethod
    async def get_topic_members(
        session: AsyncSession,
        topic_id: UUID,
        user_id: UUID
    ) -> list[TopicMember]:
        """Get all active members of a topic."""
        return await TopicMemberService.get_topic_members(session, topic_id, user_id)
    
    @staticmethod
    async def get_users_for_topic_addition(
        session: AsyncSession,
        topic_id: UUID,
        admin_id: UUID,
        search: str = None
    ) -> list[dict]:
        """Get all users with membership flag for topic addition (admin only)."""
        return await TopicMemberService.get_users_for_topic_addition(session, topic_id, admin_id, search)
    
    # ============================================================================
    # Topic Message Operations
    # ============================================================================
    
    @staticmethod
    def extract_mentions(content: str) -> list[str]:
        """Extract @mentions from message content."""
        return TopicMessageService.extract_mentions(content)
    
    @staticmethod
    async def create_message(
        session: AsyncSession,
        topic_id: UUID,
        message_data: TopicMessageCreate,
        sender_id: UUID

    ) -> TopicMessage:
        """Create a new message in a topic."""
        return await TopicMessageService.create_message(session, topic_id, message_data, sender_id)
    
    @staticmethod
    async def get_topic_messages(
        session: AsyncSession,
        topic_id: UUID,
        user_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list[TopicMessage], int]:
        """Get messages for a topic."""
        return await TopicMessageService.get_topic_messages(session, topic_id, user_id, page, page_size)
    
    @staticmethod
    async def update_message(
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID,
        content: str
    ) -> Optional[TopicMessage]:
        """Update (edit) a message."""
        return await TopicMessageService.update_message(session, message_id, user_id, content)
    
    @staticmethod
    async def delete_message(
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a message."""
        return await TopicMessageService.delete_message(session, message_id, user_id)
    
    # ============================================================================
    # Reaction Operations
    # ============================================================================
    
    @staticmethod
    async def add_reaction(
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> MessageReaction:
        """Add a reaction to a message."""
        return await TopicReactionService.add_reaction(session, message_id, user_id, emoji)
    
    @staticmethod
    async def remove_reaction(
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> bool:
        """Remove a reaction from a message."""
        return await TopicReactionService.remove_reaction(session, message_id, user_id, emoji)
    
    @staticmethod
    async def get_reaction_summary(
        session: AsyncSession,
        message_id: UUID,
        current_user_id: UUID
    ) -> list[ReactionSummary]:
        """Get reaction summary for a message grouped by emoji."""
        return await TopicReactionService.get_reaction_summary(session, message_id, current_user_id)

    @staticmethod
    async def delete_topic_by_id(
        session: AsyncSession,
        topic_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a topic and all its associated messages (admin only)."""
        return await TopicManagementService.delete_topic_by_id(session, topic_id, user_id)