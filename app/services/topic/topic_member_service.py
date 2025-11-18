"""Topic member management service."""
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.models.channel import TopicMember
from app.models.user import User, UserRole


class TopicMemberService:
    """Service for topic member operations."""
    
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
    async def add_member(
        session: AsyncSession,
        topic_id: UUID,
        admin_id: UUID,
        user_id: UUID
    ) -> TopicMember:
        """Add a member to a topic (admin only)."""
        try:
            # Verify admin
            is_admin = await TopicMemberService.verify_admin(session, admin_id)
            if not is_admin:
                raise ValueError("Only admins can add members to topics")
            
            # Check if member already exists
            existing_query = select(TopicMember).where(
                and_(
                    TopicMember.topic_id == topic_id,
                    TopicMember.user_id == user_id
                )
            )
            existing_result = await session.execute(existing_query)
            existing_member = existing_result.scalar_one_or_none()
            
            if existing_member:
                if existing_member.is_active:
                    raise ValueError("User is already a member of this topic")
                # Reactivate
                existing_member.is_active = True
                await session.commit()
                await session.refresh(existing_member)
                return existing_member
            
            # Add new member
            member = TopicMember(
                topic_id=topic_id,
                user_id=user_id,
                is_active=True
            )
            session.add(member)
            await session.commit()
            await session.refresh(member)
            
            logger.info(f"Member {user_id} added to topic {topic_id} by admin {admin_id}")
            return member
            
        except ValueError:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error adding member: {e}")
            raise
    
    @staticmethod
    async def remove_member(
        session: AsyncSession,
        topic_id: UUID,
        admin_id: UUID,
        user_id: UUID
    ) -> bool:
        """Remove a member from a topic (admin only)."""
        try:
            # Verify admin
            is_admin = await TopicMemberService.verify_admin(session, admin_id)
            if not is_admin:
                raise ValueError("Only admins can remove members from topics")
            
            # Get member
            query = select(TopicMember).where(
                and_(
                    TopicMember.topic_id == topic_id,
                    TopicMember.user_id == user_id
                )
            )
            result = await session.execute(query)
            member = result.scalar_one_or_none()
            
            if not member:
                return False
            
            # Soft delete
            member.is_active = False
            await session.commit()
            
            logger.info(f"Member {user_id} removed from topic {topic_id} by admin {admin_id}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error removing member: {e}")
            raise
    
    @staticmethod
    async def get_topic_members(
        session: AsyncSession,
        topic_id: UUID,
        user_id: UUID
    ) -> list[TopicMember]:
        """Get all active members of a topic."""
        try:
            # Verify user is a member of the topic
            member_check_query = select(TopicMember).where(
                and_(
                    TopicMember.topic_id == topic_id,
                    TopicMember.user_id == user_id,
                    TopicMember.is_active == True
                )
            )
            member_check_result = await session.execute(member_check_query)
            if not member_check_result.scalar_one_or_none():
                raise ValueError("User is not a member of this topic")
            
            # Get all active members with user info
            query = (
                select(TopicMember)
                .where(
                    and_(
                        TopicMember.topic_id == topic_id,
                        TopicMember.is_active == True
                    )
                )
                .options(selectinload(TopicMember.user))
                .order_by(TopicMember.joined_at.asc())
            )
            
            result = await session.execute(query)
            members = result.scalars().all()
            
            logger.info(f"Retrieved {len(members)} members for topic {topic_id}")
            return list(members)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error getting topic members: {e}")
            raise
    
    @staticmethod
    async def get_users_for_topic_addition(
        session: AsyncSession,
        topic_id: UUID,
        admin_id: UUID,
        search: str = None
    ) -> list[dict]:
        """
        Get all users with a flag indicating if they're already in the topic.
        Only admins can access this.
        """
        try:
            # Verify admin
            is_admin = await TopicMemberService.verify_admin(session, admin_id)
            if not is_admin:
                raise ValueError("Only admins can view users for topic addition")
            
            # Get all active users
            user_query = select(User).where(User.is_active == True)
            
            # Add search filter if provided
            if search:
                search_term = f"%{search.lower()}%"
                from sqlalchemy import func, or_
                user_query = user_query.where(
                    or_(
                        func.lower(User.email).like(search_term),
                        func.lower(User.full_name).like(search_term)
                    )
                )
            
            user_query = user_query.order_by(User.full_name.asc())
            user_result = await session.execute(user_query)
            users = user_result.scalars().all()
            
            # Get all current topic members
            member_query = select(TopicMember).where(
                and_(
                    TopicMember.topic_id == topic_id,
                    TopicMember.is_active == True
                )
            )
            member_result = await session.execute(member_query)
            members = member_result.scalars().all()
            member_user_ids = {member.user_id for member in members}
            
            # Build response with membership flag
            result = []
            for user in users:
                result.append({
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'avatar_url': None,  # User model doesn't have avatar_url yet
                    'is_member': user.id in member_user_ids
                })
            
            logger.info(f"Retrieved {len(result)} users for topic {topic_id} addition")
            return result
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error getting users for topic addition: {e}")
            raise
