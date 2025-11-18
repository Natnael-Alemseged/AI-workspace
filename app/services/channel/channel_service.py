"""Channel service for business logic."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.models.channel import Channel, Topic, TopicMember
from app.models.user import User, UserRole
from app.schemas.channel import ChannelCreate, ChannelUpdate


class ChannelService:
    """Service for channel operations (admin only)."""
    
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
    async def create_channel(
        session: AsyncSession,
        channel_data: ChannelCreate,
        creator_id: UUID
    ) -> Channel:
        """
        Create a new channel (admin only).
        
        Args:
            session: Database session
            channel_data: Channel creation data
            creator_id: ID of the admin creating the channel
            
        Returns:
            Created Channel
            
        Raises:
            ValueError: If user is not an admin or channel name exists
        """
        try:
            # Verify admin
            is_admin = await ChannelService.verify_admin(session, creator_id)
            if not is_admin:
                raise ValueError("Only admins can create channels")
            
            # Check if channel name already exists
            existing_query = select(Channel).where(
                and_(
                    Channel.name == channel_data.name,
                    Channel.is_active == True
                )
            )
            existing_result = await session.execute(existing_query)
            if existing_result.scalar_one_or_none():
                raise ValueError(f"Channel '{channel_data.name}' already exists")
            
            # Create channel
            channel = Channel(
                name=channel_data.name,
                description=channel_data.description,
                icon=channel_data.icon,
                color=channel_data.color,
                created_by=creator_id,
                is_active=True
            )
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            
            logger.info(f"Channel created: {channel.id} by admin {creator_id}")
            return channel
            
        except ValueError:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating channel: {e}")
            raise
    
    @staticmethod
    async def get_all_channels(
        session: AsyncSession,
        user_id: Optional[UUID] = None
    ) -> list[Channel]:
        """
        Get active channels where the user is a member of at least one topic.
        
        Args:
            session: Database session
            user_id: Optional user ID to filter channels by topic membership
            
        Returns:
            List of channels
        """
        try:
            if user_id:
                # Get channels where user is a member of at least one topic
                query = (
                    select(Channel)
                    .join(Topic, Channel.id == Topic.channel_id)
                    .join(TopicMember, Topic.id == TopicMember.topic_id)
                    .where(
                        and_(
                            Channel.is_active == True,
                            Topic.is_active == True,
                            TopicMember.user_id == user_id,
                            TopicMember.is_active == True
                        )
                    )
                    .distinct()
                    .order_by(Channel.name)
                )
            else:
                # Get all channels (admin view)
                query = (
                    select(Channel)
                    .where(Channel.is_active == True)
                    .order_by(Channel.name)
                )
            
            result = await session.execute(query)
            channels = result.scalars().all()
            
            return list(channels)
            
        except Exception as e:
            logger.error(f"Error getting channels: {e}")
            raise
    
    @staticmethod
    async def get_channel_by_id(
        session: AsyncSession,
        channel_id: UUID
    ) -> Optional[Channel]:
        """Get channel by ID."""
        try:
            query = (
                select(Channel)
                .where(
                    and_(
                        Channel.id == channel_id,
                        Channel.is_active == True
                    )
                )
                .options(selectinload(Channel.topics))
            )
            
            result = await session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting channel: {e}")
            raise
    
    @staticmethod
    async def update_channel(
        session: AsyncSession,
        channel_id: UUID,
        user_id: UUID,
        channel_data: ChannelUpdate
    ) -> Optional[Channel]:
        """Update channel (admin only)."""
        try:
            # Verify admin
            is_admin = await ChannelService.verify_admin(session, user_id)
            if not is_admin:
                raise ValueError("Only admins can update channels")
            
            # Get channel
            query = select(Channel).where(Channel.id == channel_id)
            result = await session.execute(query)
            channel = result.scalar_one_or_none()
            
            if not channel:
                return None
            
            # Check name uniqueness if updating name
            if channel_data.name and channel_data.name != channel.name:
                existing_query = select(Channel).where(
                    and_(
                        Channel.name == channel_data.name,
                        Channel.is_active == True,
                        Channel.id != channel_id
                    )
                )
                existing_result = await session.execute(existing_query)
                if existing_result.scalar_one_or_none():
                    raise ValueError(f"Channel '{channel_data.name}' already exists")
            
            # Update fields
            if channel_data.name is not None:
                channel.name = channel_data.name
            if channel_data.description is not None:
                channel.description = channel_data.description
            if channel_data.icon is not None:
                channel.icon = channel_data.icon
            if channel_data.color is not None:
                channel.color = channel_data.color
            
            channel.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(channel)
            
            logger.info(f"Channel updated: {channel_id} by admin {user_id}")
            return channel
            
        except ValueError:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating channel: {e}")
            raise
    
    @staticmethod
    async def delete_channel(
        session: AsyncSession,
        channel_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete (deactivate) channel (admin only)."""
        try:
            # Verify admin
            is_admin = await ChannelService.verify_admin(session, user_id)
            if not is_admin:
                raise ValueError("Only admins can delete channels")
            
            # Get channel
            query = select(Channel).where(Channel.id == channel_id)
            result = await session.execute(query)
            channel = result.scalar_one_or_none()
            
            if not channel:
                return False
            
            # Soft delete
            channel.is_active = False
            channel.updated_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(f"Channel deleted: {channel_id} by admin {user_id}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting channel: {e}")
            raise
