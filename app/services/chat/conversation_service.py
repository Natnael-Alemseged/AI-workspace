from datetime import datetime
from typing import List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    ConversationWithMessages,
    MessageCreate,
    MessageResponse,
    MessageUpdate,
)


class ConversationService:
    """Service for managing conversations and messages."""

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: UUID,
        conversation_data: ConversationCreate,
    ) -> Conversation:
        """Create a new conversation for a user."""
        conversation = Conversation(
            user_id=user_id,
            title=conversation_data.title,
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
        include_messages: bool = False,
    ) -> Optional[Conversation]:
        """Get a conversation by ID for a specific user."""
        query = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
        )
        
        if include_messages:
            query = query.options(selectinload(Conversation.messages))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        include_deleted: bool = False,
    ) -> tuple[List[Conversation], int]:
        """List all conversations for a user with pagination."""
        # Base query
        base_query = select(Conversation).where(Conversation.user_id == user_id)
        
        if not include_deleted:
            base_query = base_query.where(Conversation.deleted_at.is_(None))
        
        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = (
            base_query
            .order_by(desc(Conversation.updated_at), desc(Conversation.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        return list(conversations), total

    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
        conversation_data: ConversationUpdate,
    ) -> Optional[Conversation]:
        """Update a conversation."""
        conversation = await ConversationService.get_conversation(
            db, conversation_id, user_id
        )
        
        if not conversation:
            return None
        
        update_data = conversation_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversation, field, value)
        
        conversation.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(conversation)
        
        logger.info(f"Updated conversation {conversation_id}")
        return conversation

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
        soft_delete: bool = True,
    ) -> bool:
        """Delete a conversation (soft or hard delete)."""
        conversation = await ConversationService.get_conversation(
            db, conversation_id, user_id
        )
        
        if not conversation:
            return False
        
        if soft_delete:
            conversation.deleted_at = datetime.utcnow()
            await db.commit()
            logger.info(f"Soft deleted conversation {conversation_id}")
        else:
            await db.delete(conversation)
            await db.commit()
            logger.info(f"Hard deleted conversation {conversation_id}")
        
        return True

    @staticmethod
    async def create_message(
        db: AsyncSession,
        message_data: MessageCreate,
        user_id: UUID,
    ) -> Optional[Message]:
        """Create a new message in a conversation."""
        # Verify conversation belongs to user
        conversation = await ConversationService.get_conversation(
            db, message_data.conversation_id, user_id
        )
        
        if not conversation:
            logger.warning(
                f"Attempted to create message in non-existent conversation {message_data.conversation_id}"
            )
            return None
        
        message = Message(
            conversation_id=message_data.conversation_id,
            role=message_data.role,
            content=message_data.content,
            content_type=message_data.content_type,
            tool_name=message_data.tool_name,
            tool_input=message_data.tool_input,
            tool_output=message_data.tool_output,
            meta_data=message_data.meta_data or {},
        )
        
        db.add(message)
        
        # Update conversation's updated_at timestamp
        conversation.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(message)
        
        logger.info(
            f"Created message {message.id} in conversation {message_data.conversation_id}"
        )
        return message

    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Message]:
        """Get messages for a conversation."""
        # Verify conversation belongs to user
        conversation = await ConversationService.get_conversation(
            db, conversation_id, user_id
        )
        
        if not conversation:
            return []
        
        query = (
            select(Message)
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.is_deleted == False,
                )
            )
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_message(
        db: AsyncSession,
        message_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
        message_data: MessageUpdate,
    ) -> Optional[Message]:
        """Update a message."""
        # Verify conversation belongs to user
        conversation = await ConversationService.get_conversation(
            db, conversation_id, user_id
        )
        
        if not conversation:
            return None
        
        query = select(Message).where(
            and_(
                Message.id == message_id,
                Message.conversation_id == conversation_id,
            )
        )
        
        result = await db.execute(query)
        message = result.scalar_one_or_none()
        
        if not message:
            return None
        
        update_data = message_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(message, field, value)
        
        message.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(message)
        
        logger.info(f"Updated message {message_id}")
        return message

    @staticmethod
    async def generate_conversation_title(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Optional[str]:
        """Generate a title for a conversation based on first user message."""
        messages = await ConversationService.get_conversation_messages(
            db, conversation_id, user_id, limit=5
        )
        
        # Find first user message
        user_message = next(
            (msg for msg in messages if msg.role == MessageRole.USER),
            None
        )
        
        if user_message and user_message.content:
            # Take first 50 characters as title
            title = user_message.content[:50]
            if len(user_message.content) > 50:
                title += "..."
            
            # Update conversation title
            await ConversationService.update_conversation(
                db,
                conversation_id,
                user_id,
                ConversationUpdate(title=title),
            )
            
            return title
        
        return None

    @staticmethod
    async def get_or_create_conversation(
        db: AsyncSession,
        user_id: UUID,
        conversation_id: Optional[UUID] = None,
    ) -> Conversation:
        """Get existing conversation or create a new one."""
        if conversation_id:
            conversation = await ConversationService.get_conversation(
                db, conversation_id, user_id
            )
            if conversation:
                return conversation
        
        # Create new conversation
        conversation = await ConversationService.create_conversation(
            db, user_id, ConversationCreate()
        )
        return conversation