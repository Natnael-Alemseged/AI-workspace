"""Topic message service for message operations."""
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.ai_bots import get_bot_id_for_agent_type
from app.core.logging import logger
from app.models.channel import MessageMention, Topic, TopicMember, TopicMessage, TopicMessageAttachment
from app.models.user import PushSubscription, User, UserRole
from app.schemas.channel import TopicMessageCreate, TopicMessageRead
from app.utils.ai_agent_parser import parse_agent_mention
from app.services.chat import agent_service
from app.services.notification_service import notification_service
import asyncio

class TopicMessageService:
    """Service for topic message operations."""
    
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
    def extract_mentions(content: str) -> list[str]:
        """Extract @mentions from message content."""
        # Match @username or @"Full Name"
        pattern = r'@(\w+)|@"([^"]+)"'
        matches = re.findall(pattern, content)
        mentions = [match[0] or match[1] for match in matches]
        return mentions
    
    @staticmethod
    async def create_message(
        session: AsyncSession,
        topic_id: UUID,
        message_data: TopicMessageCreate,
        sender_id: UUID
    ) -> TopicMessage:
        """Create a new message in a topic."""
        try:
            # Verify user is a member
            member_query = select(TopicMember).where(
                and_(
                    TopicMember.topic_id == topic_id,
                    TopicMember.user_id == sender_id,
                    TopicMember.is_active == True
                )
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()


            
            if not member:
                raise ValueError("User is not a member of this topic")
            
            # Store original message content (AI processing will be async)
            message_content = message_data.content
            
            # Create message
            message = TopicMessage(
                topic_id=topic_id,
                sender_id=sender_id,
                content=message_content,
                reply_to_id=message_data.reply_to_id,
                is_edited=False,
                is_deleted=False
            )
            session.add(message)
            await session.flush()
            
            # Update sender's read status to prevent unread indicator for own message
            await session.refresh(message, ["created_at"])
            member.last_read_at = message.created_at
            member.unread_count = 0
            session.add(member)
            
            # Create attachment records if any
            if message_data.attachments:
                for attachment_data in message_data.attachments:
                    attachment = TopicMessageAttachment(
                        message_id=message.id,
                        url=attachment_data.url,
                        filename=attachment_data.filename,
                        size=attachment_data.size,
                        mime_type=attachment_data.mime_type
                    )
                    session.add(attachment)
                await session.flush()
            
            # Process mentions
            mentioned_user_ids = set(message_data.mentioned_user_ids)
            
            # Also extract mentions from content
            mention_names = TopicMessageService.extract_mentions(message_data.content)
            if mention_names:
                # Find users by email or full_name
                user_query = select(User).where(
                    or_(
                        User.email.in_(mention_names),
                        User.full_name.in_(mention_names)
                    )
                )
                user_result = await session.execute(user_query)
                mentioned_users = user_result.scalars().all()
                mentioned_user_ids.update([user.id for user in mentioned_users])
            
            # Create mention records
            for mentioned_user_id in mentioned_user_ids:
                # Verify mentioned user is a member
                mentioned_member_query = select(TopicMember).where(
                    and_(
                        TopicMember.topic_id == topic_id,
                        TopicMember.user_id == mentioned_user_id,
                        TopicMember.is_active == True
                    )
                )
                mentioned_member_result = await session.execute(mentioned_member_query)
                if mentioned_member_result.scalar_one_or_none():
                    mention = MessageMention(
                        message_id=message.id,
                        mentioned_user_id=mentioned_user_id,
                        is_read=False
                    )
                    session.add(mention)
            
            # Update topic's updated_at
            topic_query = select(Topic).where(Topic.id == topic_id)
            topic_result = await session.execute(topic_query)
            topic = topic_result.scalar_one_or_none()
            
            topic_name = "Unknown Topic"
            if topic:
                topic.updated_at = datetime.utcnow()
                topic_name = topic.name

            await session.commit()
            
            # Load relationships to prevent lazy loading errors
            # Use a select statement with options to ensure relationships are loaded
            # session.refresh doesn't always handle relationships correctly in async
            message_query = (
                select(TopicMessage)
                .where(TopicMessage.id == message.id)
                .options(
                    selectinload(TopicMessage.sender),
                    selectinload(TopicMessage.mentions),
                    selectinload(TopicMessage.reactions),
                    selectinload(TopicMessage.attachments)
                )
            )
            message_result = await session.execute(message_query)
            message = message_result.scalar_one()
            
            logger.info(f"Message created: {message.id} in topic {topic_id}")

            # ADD YOUR PRINT HERE — PERFECT SPOT
            print("\nMessage Attachments:")
            if message.attachments:
                for attachment in message.attachments:
                    print({
                        "id": attachment.id,
                        "filename": attachment.filename,
                        "url": attachment.url,
                        "size": attachment.size,
                        "mime_type": attachment.mime_type
                    })
            else:
                print("  No attachments")
            print(f"Total attachments: {len(message.attachments)}")
            # END OF PRINT
            
            # Check if message contains AI agent mention (process async)
            agent_mention = parse_agent_mention(message_data.content)
            if agent_mention:
                logger.info(f"AI agent detected: {agent_mention.agent_type}, will process asynchronously")
                # Return message immediately, AI will process in background
                # The background task will be triggered by the route handler

            logger.info(f"Message created: {message.id} in topic {topic_id}")

            # 🔥 Send push notification to other members
            member_query = select(TopicMember.user_id).where(
                and_(
                    TopicMember.topic_id == topic_id,
                    TopicMember.is_active == True,
                    TopicMember.user_id != sender_id
                )
            )
            result = await session.execute(member_query)
            receiver_ids = result.scalars().all()

            # Fetch all push subscriptions for topic members (users can have multiple devices)
            if receiver_ids:
                subscription_query = select(PushSubscription).where(
                    PushSubscription.user_id.in_(receiver_ids)
                )
                sub_result = await session.execute(subscription_query)
                subscriptions = sub_result.scalars().all()

                # Send push notifications (await to ensure session remains valid)
                notification_tasks = []
                for subscription in subscriptions:
                    # Pass FCM token directly
                    task = notification_service.send_message_notification(
                        subscription_info=subscription.endpoint,
                        sender_name=message.sender.full_name,
                        message_preview=message_content,
                        topic_name=topic_name,
                        topic_id=str(topic_id),
                    )
                    notification_tasks.append(task)

                # Execute all notifications concurrently
                if notification_tasks:
                    await asyncio.gather(*notification_tasks, return_exceptions=True)
                    logger.info(f"📨 Push notifications sent for {len(notification_tasks)} subscriptions across {len(receiver_ids)} users")
            
            return message
            
        except ValueError:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating message: {e}")
            raise
    
    @staticmethod
    async def create_ai_message(
        session: AsyncSession,
        topic_id: UUID,
        content: str,
        reply_to_id: UUID,
        agent_type: str = "general"
    ) -> TopicMessage:
        """Create an AI response message using the bot user ID."""
        try:
            # Get the bot user ID for this agent type
            bot_id = get_bot_id_for_agent_type(agent_type)
            
            # Create AI message with bot user as sender
            message = TopicMessage(
                topic_id=topic_id,
                sender_id=bot_id,
                content=content,
                reply_to_id=reply_to_id,
                is_edited=False,
                is_deleted=False
            )
            session.add(message)
            
            # Update topic's updated_at
            topic_query = select(Topic).where(Topic.id == topic_id)
            topic_result = await session.execute(topic_query)
            topic = topic_result.scalar_one_or_none()
            if topic:
                topic.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(message)
            
            logger.info(f"AI message created: {message.id} in topic {topic_id}")
            return message
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating AI message: {e}")
            raise
    
    @staticmethod
    async def get_topic_messages(
        session: AsyncSession,
        topic_id: UUID,
        user_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list[TopicMessage], int]:
        """Get messages for a topic."""
        try:
            # Verify user is a member
            member_query = select(TopicMember).where(
                and_(
                    TopicMember.topic_id == topic_id,
                    TopicMember.user_id == user_id,
                    TopicMember.is_active == True
                )
            )
            member_result = await session.execute(member_query)
            if not member_result.scalar_one_or_none():
                raise ValueError("User is not a member of this topic")
            
            # Count total
            count_query = (
                select(func.count(TopicMessage.id))
                .where(
                    and_(
                        TopicMessage.topic_id == topic_id,
                        TopicMessage.is_deleted == False
                    )
                )
            )
            total_result = await session.execute(count_query)
            total = total_result.scalar_one()
            
            # Get messages
            offset = (page - 1) * page_size
            query = (
                select(TopicMessage)
                .where(
                    and_(
                        TopicMessage.topic_id == topic_id,
                        TopicMessage.is_deleted == False
                    )
                )
                .order_by(TopicMessage.created_at.desc())
                .offset(offset)
                .limit(page_size)
                .options(
                    selectinload(TopicMessage.sender),
                    selectinload(TopicMessage.mentions),
                    selectinload(TopicMessage.reactions),
                    selectinload(TopicMessage.attachments)
                )
            )
            
            result = await session.execute(query)
            messages = result.scalars().all()

            # THIS IS THE KEY FIX:
            pydantic_messages = [
                TopicMessageRead.model_validate(msg)  # ← Convert each ORM object
                for msg in messages
            ]

            return pydantic_messages, total
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            raise
    
    @staticmethod
    async def update_message(
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID,
        content: str
    ) -> Optional[TopicMessage]:
        """Update (edit) a message."""
        try:
            # Get message
            query = select(TopicMessage).where(TopicMessage.id == message_id)
            result = await session.execute(query)
            message = result.scalar_one_or_none()
            
            if not message:
                return None
            
            # Verify sender
            if message.sender_id != user_id:
                raise ValueError("Only the sender can edit this message")
            
            # Update message
            message.content = content
            message.is_edited = True
            message.edited_at = datetime.utcnow()
            
            await session.commit()
            
            # Load relationships to prevent lazy loading errors
            message_query = (
                select(TopicMessage)
                .where(TopicMessage.id == message.id)
                .options(
                    selectinload(TopicMessage.sender),
                    selectinload(TopicMessage.mentions),
                    selectinload(TopicMessage.reactions),
                    selectinload(TopicMessage.attachments)
                )
            )
            message_result = await session.execute(message_query)
            message = message_result.scalar_one()
            
            logger.info(f"Message updated: {message_id}")
            return message
            
        except ValueError:
            raise
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
        """Delete a message."""
        try:
            # Get message
            query = select(TopicMessage).where(TopicMessage.id == message_id)
            result = await session.execute(query)
            message = result.scalar_one_or_none()
            
            if not message:
                return False
            
            # Verify sender or admin
            is_admin = await TopicMessageService.verify_admin(session, user_id)
            if message.sender_id != user_id and not is_admin:
                raise ValueError("Only the sender or an admin can delete this message")
            
            # Soft delete
            message.is_deleted = True
            message.deleted_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(f"Message deleted: {message_id}")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting message: {e}")
            raise
