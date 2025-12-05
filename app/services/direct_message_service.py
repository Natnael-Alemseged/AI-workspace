"""Service layer for Direct Message operations."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.logging import logger
from app.models.direct_message import (
    DirectMessage,
    DirectMessageAttachment,
    DirectMessageReaction,
)
from app.models.user import PushSubscription, User
from app.schemas.direct_message import AttachmentData, ReactionSummary
from app.services.notification_service import notification_service


class DirectMessageService:
    """Service for managing direct messages."""
    
    async def send_message(
        self,
        session: AsyncSession,
        sender_id: UUID,
        receiver_id: UUID,
        content: str,
        reply_to_id: Optional[UUID] = None,
        attachments: Optional[list[AttachmentData]] = None
    ) -> DirectMessage:
        """
        Send a direct message to another user.
        
        Args:
            session: Database session
            sender_id: ID of the sender
            receiver_id: ID of the receiver
            content: Message content
            reply_to_id: Optional ID of message being replied to
            attachments: Optional list of file attachments
            
        Returns:
            Created DirectMessage instance
        """
        # Verify receiver exists and is not a bot
        result = await session.execute(
            select(User).where(User.id == receiver_id)
        )
        receiver = result.scalar_one_or_none()
        
        if not receiver:
            raise ValueError("Receiver not found")
        
        if receiver.is_bot:
            raise ValueError("Cannot send direct messages to bots")
        
        # Create message
        message = DirectMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            reply_to_id=reply_to_id
        )
        
        session.add(message)
        await session.flush()
        
        # Add attachments if provided
        if attachments:
            for attachment_data in attachments:
                attachment = DirectMessageAttachment(
                    message_id=message.id,
                    url=attachment_data.url,
                    filename=attachment_data.filename,
                    size=attachment_data.size,
                    mime_type=attachment_data.mime_type
                )
                session.add(attachment)
        
        await session.commit()
        
        # Reload message with all relationships eagerly loaded
        # Note: sender and receiver are automatically eager loaded via lazy="joined" on the model
        message_query = select(DirectMessage).where(
            DirectMessage.id == message.id
        ).options(
            selectinload(DirectMessage.sender),
            selectinload(DirectMessage.receiver),
            selectinload(DirectMessage.attachments),
            selectinload(DirectMessage.reactions)
        )
        result = await session.execute(message_query)
        message = result.scalar_one()
        
        # Send push notification to receiver
        await self._send_new_message_notification(
            session=session,
            message=message,
            sender_id=sender_id,
            receiver_id=receiver_id
        )
        
        return message
    
    async def get_messages(
        self,
        session: AsyncSession,
        user_id: UUID,
        other_user_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[list[DirectMessage], int]:
        """
        Get messages between two users with pagination.
        
        Args:
            session: Database session
            user_id: Current user ID
            other_user_id: Other user ID
            page: Page number (1-indexed)
            page_size: Number of messages per page
            
        Returns:
            Tuple of (messages list, total count)
        """
        # Build query for messages between the two users
        # Note: sender and receiver are automatically eager loaded via lazy="joined" on the model
        query = select(DirectMessage).where(
            or_(
                and_(
                    DirectMessage.sender_id == user_id,
                    DirectMessage.receiver_id == other_user_id
                ),
                and_(
                    DirectMessage.sender_id == other_user_id,
                    DirectMessage.receiver_id == user_id
                )
            ),
            DirectMessage.is_deleted == False
        ).options(
            selectinload(DirectMessage.sender),
            selectinload(DirectMessage.receiver),
            selectinload(DirectMessage.attachments),
            selectinload(DirectMessage.reactions).joinedload(DirectMessageReaction.user)
        ).order_by(desc(DirectMessage.created_at))
        
        # Get total count
        count_query = select(func.count()).select_from(DirectMessage).where(
            or_(
                and_(
                    DirectMessage.sender_id == user_id,
                    DirectMessage.receiver_id == other_user_id
                ),
                and_(
                    DirectMessage.sender_id == other_user_id,
                    DirectMessage.receiver_id == user_id
                )
            ),
            DirectMessage.is_deleted == False
        )
        
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await session.execute(query)
        messages = result.scalars().all()
        
        # Mark messages as read for the current user
        await self._mark_messages_as_read(session, user_id, other_user_id)
        
        return list(messages), total
    
    async def get_conversations(
        self,
        session: AsyncSession,
        user_id: UUID
    ) -> list[dict]:
        """
        Get all conversations for a user with last message and unread count.
        
        Args:
            session: Database session
            user_id: Current user ID
            
        Returns:
            List of conversation dictionaries
        """
        # Get all messages involving the user
        messages_query = (
            select(DirectMessage)
            .where(
                or_(
                    DirectMessage.sender_id == user_id,
                    DirectMessage.receiver_id == user_id
                ),
                DirectMessage.is_deleted == False
            )
            .options(
                selectinload(DirectMessage.sender),
                selectinload(DirectMessage.receiver),
                selectinload(DirectMessage.attachments),
                selectinload(DirectMessage.reactions)
            )
            .order_by(desc(DirectMessage.created_at))
        )
        
        result = await session.execute(messages_query)
        all_messages = list(result.scalars().all())
        
        # Return empty list if no messages
        if not all_messages:
            return []
        
        # Get all unique conversation partner IDs
        conversation_partner_ids = set()
        for message in all_messages:
            partner_id = message.receiver_id if message.sender_id == user_id else message.sender_id
            conversation_partner_ids.add(partner_id)
        
        # Fetch all unread counts in a single query
        unread_counts_dict = {}
        if conversation_partner_ids:
            unread_counts_query = (
                select(
                    DirectMessage.sender_id,
                    func.count(DirectMessage.id).label('unread_count')
                )
                .where(
                    DirectMessage.receiver_id == user_id,
                    DirectMessage.sender_id.in_(conversation_partner_ids),
                    DirectMessage.is_read == False,
                    DirectMessage.is_deleted == False
                )
                .group_by(DirectMessage.sender_id)
            )
            
            unread_result = await session.execute(unread_counts_query)
            unread_counts_dict = {row[0]: row[1] for row in unread_result.all()}
        
        # Group messages by conversation partner
        conversations_map = {}
        
        for message in all_messages:
            # Determine the other user ID
            other_user_id = message.receiver_id if message.sender_id == user_id else message.sender_id
            
            # Skip if we already have a conversation with this user
            if other_user_id in conversations_map:
                continue
            
            # Get the other user object (already loaded via selectinload)
            other_user = message.receiver if message.sender_id == user_id else message.sender
            
            # Serialize user data to avoid lazy loading when returning to routers
            other_user_data = {
                "id": other_user.id,
                "email": other_user.email,
                "full_name": other_user.full_name,
                "is_online": other_user.is_online,
                "last_seen_at": other_user.last_seen_at,
            } if other_user else None
            
            # Serialize last message data to primitives only
            last_message_data = {
                "id": message.id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "content": message.content,
                "reply_to_id": message.reply_to_id,
                "is_read": message.is_read,
                "read_at": message.read_at,
                "is_edited": message.is_edited,
                "edited_at": message.edited_at,
                "is_deleted": message.is_deleted,
                "deleted_at": message.deleted_at,
                "created_at": message.created_at,
                "attachments": [
                    {
                        "id": attachment.id,
                        "url": attachment.url,
                        "filename": attachment.filename,
                        "size": attachment.size,
                        "mime_type": attachment.mime_type,
                        "created_at": attachment.created_at,
                    }
                    for attachment in getattr(message, "attachments", []) or []
                ],
                "reactions": [],
            }
            
            sender_obj = getattr(message, "sender", None)
            receiver_obj = getattr(message, "receiver", None)
            if sender_obj:
                last_message_data["sender_email"] = sender_obj.email
                last_message_data["sender_full_name"] = sender_obj.full_name
            if receiver_obj:
                last_message_data["receiver_email"] = receiver_obj.email
                last_message_data["receiver_full_name"] = receiver_obj.full_name
            
            # Get unread count from pre-fetched dict
            unread_count = unread_counts_dict.get(other_user_id, 0)
            
            conversations_map[other_user_id] = {
                'user': other_user_data,
                'last_message': last_message_data,
                'unread_count': unread_count,
                'last_message_at': message.created_at
            }
        
        # Convert to list and sort by last message time
        conversations = list(conversations_map.values())
        conversations.sort(key=lambda x: x['last_message_at'], reverse=True)
        
        return conversations
    
    async def get_eligible_users(
        self,
        session: AsyncSession,
        current_user_id: UUID,
        search: Optional[str] = None
    ) -> list[User]:
        """
        Get all non-bot users that can be messaged.
        
        Args:
            session: Database session
            current_user_id: Current user ID
            search: Optional search term for filtering users
            
        Returns:
            List of eligible users
        """
        query = select(User).where(
            User.is_bot == False,
            User.is_active == True,
            User.id != current_user_id
        )
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term)
                )
            )
        
        query = query.order_by(User.full_name, User.email)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def mark_message_as_read(
        self,
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Mark a specific message as read.
        
        Args:
            session: Database session
            message_id: Message ID
            user_id: Current user ID (must be receiver)
            
        Returns:
            True if marked as read, False otherwise
        """
        result = await session.execute(
            select(DirectMessage).where(
                DirectMessage.id == message_id,
                DirectMessage.receiver_id == user_id,
                DirectMessage.is_read == False
            )
        )
        message = result.scalar_one_or_none()
        
        if message:
            message.is_read = True
            message.read_at = datetime.utcnow()
            await session.commit()
            return True
        
        return False
    
    async def _mark_messages_as_read(
        self,
        session: AsyncSession,
        user_id: UUID,
        sender_id: UUID
    ) -> None:
        """Mark all unread messages from a sender as read."""
        result = await session.execute(
            select(DirectMessage).where(
                DirectMessage.sender_id == sender_id,
                DirectMessage.receiver_id == user_id,
                DirectMessage.is_read == False
            )
        )
        messages = result.scalars().all()
        
        for message in messages:
            message.is_read = True
            message.read_at = datetime.utcnow()
        
        if messages:
            await session.commit()
    
    async def update_message(
        self,
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID,
        content: str
    ) -> Optional[DirectMessage]:
        """
        Update (edit) a message.
        
        Args:
            session: Database session
            message_id: Message ID
            user_id: Current user ID (must be sender)
            content: New content
            
        Returns:
            Updated message or None if not found/unauthorized
        """
        result = await session.execute(
            select(DirectMessage).where(
                DirectMessage.id == message_id,
                DirectMessage.sender_id == user_id
            ).options(
                selectinload(DirectMessage.attachments)
            )
        )
        message = result.scalar_one_or_none()
        
        if message:
            message.content = content
            message.is_edited = True
            message.edited_at = datetime.utcnow()
            await session.commit()
            await session.refresh(message)
        
        return message
    
    async def delete_message(
        self,
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete (soft delete) a message.
        
        Args:
            session: Database session
            message_id: Message ID
            user_id: Current user ID (must be sender)
            
        Returns:
            True if deleted, False otherwise
        """
        result = await session.execute(
            select(DirectMessage).where(
                DirectMessage.id == message_id,
                DirectMessage.sender_id == user_id
            )
        )
        message = result.scalar_one_or_none()
        
        if message:
            message.is_deleted = True
            message.deleted_at = datetime.utcnow()
            await session.commit()
            return True
        
        return False
    
    async def add_reaction(
        self,
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> DirectMessageReaction:
        """
        Add a reaction to a message.
        
        Args:
            session: Database session
            message_id: Message ID
            user_id: Current user ID
            emoji: Emoji to react with
            
        Returns:
            Created reaction
        """
        # Check if reaction already exists
        result = await session.execute(
            select(DirectMessageReaction).where(
                DirectMessageReaction.message_id == message_id,
                DirectMessageReaction.user_id == user_id,
                DirectMessageReaction.emoji == emoji
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
        
        # Create new reaction
        reaction = DirectMessageReaction(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji
        )
        
        session.add(reaction)
        await session.commit()
        await session.refresh(reaction)
        
        return reaction
    
    async def remove_reaction(
        self,
        session: AsyncSession,
        message_id: UUID,
        user_id: UUID,
        emoji: str
    ) -> bool:
        """
        Remove a reaction from a message.
        
        Args:
            session: Database session
            message_id: Message ID
            user_id: Current user ID
            emoji: Emoji to remove
            
        Returns:
            True if removed, False otherwise
        """
        result = await session.execute(
            select(DirectMessageReaction).where(
                DirectMessageReaction.message_id == message_id,
                DirectMessageReaction.user_id == user_id,
                DirectMessageReaction.emoji == emoji
            )
        )
        reaction = result.scalar_one_or_none()
        
        if reaction:
            await session.delete(reaction)
            await session.commit()
            return True
        
        return False
    
    async def get_reaction_summary(
        self,
        session: AsyncSession,
        message_id: UUID,
        current_user_id: UUID
    ) -> list[ReactionSummary]:
        """
        Get reaction summary for a message.
        
        Args:
            session: Database session
            message_id: Message ID
            current_user_id: Current user ID
            
        Returns:
            List of reaction summaries
        """
        result = await session.execute(
            select(DirectMessageReaction).where(
                DirectMessageReaction.message_id == message_id
            )
        )
        reactions = result.scalars().all()
        
        # Group by emoji
        emoji_map = {}
        for reaction in reactions:
            if reaction.emoji not in emoji_map:
                emoji_map[reaction.emoji] = {
                    'emoji': reaction.emoji,
                    'count': 0,
                    'users': [],
                    'user_reacted': False
                }
            
            emoji_map[reaction.emoji]['count'] += 1
            emoji_map[reaction.emoji]['users'].append(reaction.user_id)
            
            if reaction.user_id == current_user_id:
                emoji_map[reaction.emoji]['user_reacted'] = True
        
        return [
            ReactionSummary(**data) 
            for data in emoji_map.values()
        ]
    
    async def _send_new_message_notification(
        self,
        session: AsyncSession,
        message: DirectMessage,
        sender_id: UUID,
        receiver_id: UUID
    ) -> None:
        """Send push notification for new message."""
        try:
            # Get sender info
            sender_result = await session.execute(
                select(User).where(User.id == sender_id)
            )
            sender = sender_result.scalar_one_or_none()
            
            if not sender:
                return
            
            # Get receiver's push subscriptions
            subscriptions_result = await session.execute(
                select(PushSubscription).where(
                    PushSubscription.user_id == receiver_id
                )
            )
            subscriptions = subscriptions_result.scalars().all()
            
            if not subscriptions:
                return
            
            # Prepare notification
            sender_name = sender.full_name or sender.email
            message_preview = message.content[:100] + "..." if len(message.content) > 100 else message.content
            
            # Send to all subscriptions
            for subscription in subscriptions:
                await notification_service.send_notification(
                    subscription_info=subscription.endpoint,
                    title=f"New message from {sender_name}",
                    body=message_preview,
                    data={
                        "type": "direct_message",
                        "sender_id": str(sender_id),
                        "message_id": str(message.id),
                        "sender_name": sender_name
                    }
                )
        
        except Exception as e:
            logger.error(f"Error sending DM notification: {e}")


# Global service instance
direct_message_service = DirectMessageService()
