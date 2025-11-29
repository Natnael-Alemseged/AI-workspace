"""Topic management service for CRUD operations."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.ai_bots import EMAIL_AI_BOT_ID, GENERAL_AI_BOT_ID, SEARCH_AI_BOT_ID
from app.core.logging import logger
from app.models.channel import Topic, TopicMember
from app.models.user import User, UserRole
from app.schemas.channel import TopicCreate, TopicUpdate


class TopicManagementService:
    """Service for topic CRUD operations."""
    
    @staticmethod
    async def verify_admin(session: AsyncSession, user_id: UUID) -> bool:
        """Verify if user is an admin."""
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        return user.role == UserRole.ADMIN or user.is_superuser
    
    @staticmethod
    async def create_topic(
        session: AsyncSession,
        topic_data: TopicCreate,
        creator_id: UUID
    ) -> Topic:
        """
        Create a new topic (admin only).
        
        Args:
            session: Database session
            topic_data: Topic creation data
            creator_id: ID of the admin creating the topic
            
        Returns:
            Created Topic
            
        Raises:
            ValueError: If user is not an admin
        """
        try:
            # Verify admin
            is_admin = await TopicManagementService.verify_admin(session, creator_id)
            if not is_admin:
                raise ValueError("Only admins can create topics")
            
            # Create topic
            topic = Topic(
                channel_id=topic_data.channel_id,
                name=topic_data.name,
                description=topic_data.description,
                created_by=creator_id,
                is_active=True,
                is_pinned=False
            )
            session.add(topic)
            await session.flush()
            
            # Add members (including creator and AI bots)
            all_member_ids = set(topic_data.member_ids)
            all_member_ids.add(creator_id)
            
            # Automatically add all AI bots to every topic
            all_member_ids.add(EMAIL_AI_BOT_ID)
            all_member_ids.add(SEARCH_AI_BOT_ID)
            all_member_ids.add(GENERAL_AI_BOT_ID)
            
            for member_id in all_member_ids:
                member = TopicMember(
                    topic_id=topic.id,
                    user_id=member_id,
                    is_active=True
                )
                session.add(member)
            
            logger.info(f"Added {len(all_member_ids)} members to topic (including 3 AI bots)")
            
            await session.commit()
            
            # Reload topic with members
            query = select(Topic).where(Topic.id == topic.id).options(
                selectinload(Topic.members).selectinload(TopicMember.user)
            )
            result = await session.execute(query)
            topic = result.scalar_one()
            
            logger.info(f"Topic created: {topic.id} by admin {creator_id}")
            return topic
            
        except ValueError:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating topic: {e}")
            raise
    
    @staticmethod
    async def get_channel_topics(
        session: AsyncSession,
        channel_id: UUID,
        page: int = 1,
        page_size: int = 50,
        user_id: Optional[UUID] = None
    ) -> tuple[list[Topic], int]:
        """Get topics in a channel that the user is a member of."""
        try:
            # Base query - join with topic_members to filter by user membership
            base_conditions = [
                Topic.channel_id == channel_id,
                Topic.is_active == True
            ]
            
            # If user_id provided, only show topics they're a member of
            if user_id:
                # Count total topics user is a member of
                count_query = (
                    select(func.count(Topic.id))
                    .join(TopicMember, Topic.id == TopicMember.topic_id)
                    .where(
                        and_(
                            *base_conditions,
                            TopicMember.user_id == user_id,
                            TopicMember.is_active == True
                        )
                    )
                )
            else:
                # Count all topics in channel (admin view)
                count_query = (
                    select(func.count(Topic.id))
                    .where(and_(*base_conditions))
                )
            
            total_result = await session.execute(count_query)
            total = total_result.scalar_one()
            
            # Get topics
            offset = (page - 1) * page_size
            
            if user_id:
                # Get topics user is a member of
                query = (
                    select(Topic)
                    .join(TopicMember, Topic.id == TopicMember.topic_id)
                    .where(
                        and_(
                            *base_conditions,
                            TopicMember.user_id == user_id,
                            TopicMember.is_active == True
                        )
                    )
                    .order_by(Topic.is_pinned.desc(), Topic.updated_at.desc())
                    .offset(offset)
                    .limit(page_size)
                )
            else:
                # Get all topics (admin view)
                query = (
                    select(Topic)
                    .where(and_(*base_conditions))
                    .order_by(Topic.is_pinned.desc(), Topic.updated_at.desc())
                    .offset(offset)
                    .limit(page_size)
                )
            
            result = await session.execute(query)
            topics = result.scalars().all()
            
            return list(topics), total
            
        except Exception as e:
            logger.error(f"Error getting channel topics: {e}")
            raise
    
    @staticmethod
    async def get_user_topics(
        session: AsyncSession,
        user_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list[Topic], int]:
        """Get all topics a user is a member of."""
        try:
            # Count total
            count_query = (
                select(func.count(Topic.id))
                .join(TopicMember, Topic.id == TopicMember.topic_id)
                .where(
                    and_(
                        TopicMember.user_id == user_id,
                        TopicMember.is_active == True,
                        Topic.is_active == True
                    )
                )
            )
            total_result = await session.execute(count_query)
            total = total_result.scalar_one()
            
            # Get topics
            offset = (page - 1) * page_size
            query = (
                select(Topic)
                .join(TopicMember, Topic.id == TopicMember.topic_id)
                .where(
                    and_(
                        TopicMember.user_id == user_id,
                        TopicMember.is_active == True,
                        Topic.is_active == True
                    )
                )
                .order_by(Topic.updated_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            
            result = await session.execute(query)
            topics = result.scalars().unique().all()
            
            # Calculate unread_count for each topic efficiently
            if topics:
                from app.models.channel import TopicMessage
                from sqlalchemy import case, literal_column
                
                # Get last_read_at for each topic for this user
                topic_ids = [topic.id for topic in topics]
                
                # Single optimized query to calculate unread counts for all topics
                # Uses a subquery to join topic_members and count messages conditionally
                unread_subquery = (
                    select(
                        TopicMessage.topic_id,
                        func.sum(
                            case(
                                # If last_read_at is NULL or message is after last_read_at, count it
                                (
                                    (TopicMember.last_read_at == None) | 
                                    (TopicMessage.created_at > TopicMember.last_read_at),
                                    1
                                ),
                                else_=0
                            )
                        ).label('unread_count')
                    )
                    .select_from(TopicMessage)
                    .outerjoin(
                        TopicMember,
                        and_(
                            TopicMessage.topic_id == TopicMember.topic_id,
                            TopicMember.user_id == user_id
                        )
                    )
                    .where(TopicMessage.topic_id.in_(topic_ids))
                    .group_by(TopicMessage.topic_id)
                )
                
                unread_result = await session.execute(unread_subquery)
                unread_counts = {row[0]: row[1] or 0 for row in unread_result.all()}
                
                # Set unread_count for each topic
                for topic in topics:
                    topic.unread_count = unread_counts.get(topic.id, 0)
            
            return list(topics), total
            
        except Exception as e:
            logger.error(f"Error getting user topics: {e}")
            raise
    
    @staticmethod
    async def get_topic_by_id(
        session: AsyncSession,
        topic_id: UUID,
        user_id: UUID
    ) -> Optional[Topic]:
        """Get topic by ID if user is a member."""
        try:
            query = (
                select(Topic)
                .join(TopicMember, Topic.id == TopicMember.topic_id)
                .where(
                    and_(
                        Topic.id == topic_id,
                        TopicMember.user_id == user_id,
                        TopicMember.is_active == True,
                        Topic.is_active == True
                    )
                )
                .options(
                    selectinload(Topic.members).selectinload(TopicMember.user)
                )
            )
            
            result = await session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting topic: {e}")
            raise
    
    @staticmethod
    async def update_topic(
        session: AsyncSession,
        topic_id: UUID,
        user_id: UUID,
        topic_data: TopicUpdate
    ) -> Optional[Topic]:
        """Update topic (admin only)."""
        try:
            # Verify admin
            is_admin = await TopicManagementService.verify_admin(session, user_id)
            if not is_admin:
                raise ValueError("Only admins can update topics")
            
            # Get topic
            query = select(Topic).where(Topic.id == topic_id)
            result = await session.execute(query)
            topic = result.scalar_one_or_none()
            
            if not topic:
                return None
            
            # Update fields
            if topic_data.name is not None:
                topic.name = topic_data.name
            if topic_data.description is not None:
                topic.description = topic_data.description
            if topic_data.is_pinned is not None:
                topic.is_pinned = topic_data.is_pinned
            
            topic.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(topic)
            
            logger.info(f"Topic updated: {topic_id} by admin {user_id}")
            return topic
            
        except ValueError:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating topic: {e}")
            raise

    @staticmethod
    async def delete_topic_by_id(
        session: AsyncSession,
        topic_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a topic and all its associated messages (admin only).
        
        Args:
            session: Database session
            topic_id: ID of the topic to delete
            user_id: ID of the admin requesting deletion
            
        Returns:
            True if topic was deleted, False if not found
            
        Raises:
            ValueError: If user is not an admin
        """
        try:
            # Verify admin
            is_admin = await TopicManagementService.verify_admin(session, user_id)
            if not is_admin:
                raise ValueError("Only admins can delete topics")
            
            # Get topic
            query = select(Topic).where(Topic.id == topic_id)
            result = await session.execute(query)
            topic = result.scalar_one_or_none()
            
            if not topic:
                return False
            
            # Import TopicMessage model
            from app.models.channel import TopicMessage
            
            # First, get all messages in the topic
            delete_messages_query = select(TopicMessage).where(TopicMessage.topic_id == topic_id)
            messages_result = await session.execute(delete_messages_query)
            messages = messages_result.scalars().all()
            
            # Step 1: Set all reply_to_id to NULL to avoid foreign key constraint violations
            for message in messages:
                message.reply_to_id = None
            
            await session.flush()
            
            # Step 2: Now delete all messages (cascade will handle mentions and reactions)
            for message in messages:
                await session.delete(message)
            
            logger.info(f"Deleted {len(messages)} messages from topic {topic_id}")
            
            # Delete all topic members
            delete_members_query = select(TopicMember).where(TopicMember.topic_id == topic_id)
            members_result = await session.execute(delete_members_query)
            members = members_result.scalars().all()
            
            for member in members:
                await session.delete(member)
            
            logger.info(f"Deleted {len(members)} members from topic {topic_id}")
            
            # Delete the topic itself
            await session.delete(topic)
            
            await session.commit()
            
            logger.info(f"Topic deleted: {topic_id} by admin {user_id}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting topic: {e}")
            raise





