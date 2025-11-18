from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.user import User
from app.schemas.conversation import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    ConversationWithMessages,
    MessageCreate,
    MessageResponse,
    MessageUpdate,
)
from app.services.chat import ConversationService

# Import current user dependency - adjust based on your auth setup
try:
    from app.api.routes.users_complete import get_current_active_user as current_active_user
except ImportError:
    from app.api.routes.auth import current_active_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


# -------------------- Conversation Endpoints --------------------

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Create a new conversation session."""
    try:
        conversation = await ConversationService.create_conversation(
            db, user.id, conversation_data
        )
        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            deleted_at=conversation.deleted_at,
            message_count=0,
        )
    except Exception as e:
        logger.error(f"Error creating conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_deleted: bool = Query(False, description="Include deleted conversations"),
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """List all conversations for the current user with pagination."""
    try:
        skip = (page - 1) * page_size
        conversations, total = await ConversationService.list_conversations(
            db, user.id, skip=skip, limit=page_size, include_deleted=include_deleted
        )
        
        # Convert to response models
        conversation_responses = []
        for conv in conversations:
            # Count messages for each conversation
            messages = await ConversationService.get_conversation_messages(
                db, conv.id, user.id, limit=1
            )
            message_count = len(messages) if messages else 0
            
            conversation_responses.append(
                ConversationResponse(
                    id=conv.id,
                    user_id=conv.user_id,
                    title=conv.title,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    deleted_at=conv.deleted_at,
                    message_count=message_count,
                )
            )
        
        has_more = (skip + page_size) < total
        
        return ConversationListResponse(
            conversations=conversation_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )
    except Exception as e:
        logger.error(f"Error listing conversations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations",
        )


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    include_messages: bool = Query(True, description="Include messages in response"),
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Get a specific conversation by ID."""
    try:
        conversation = await ConversationService.get_conversation(
            db, conversation_id, user.id, include_messages=include_messages
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        messages = []
        if include_messages:
            messages = await ConversationService.get_conversation_messages(
                db, conversation_id, user.id
            )
        
        return ConversationWithMessages(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            deleted_at=conversation.deleted_at,
            message_count=len(messages),
            messages=[
                MessageResponse(
                    id=msg.id,
                    conversation_id=msg.conversation_id,
                    role=msg.role,
                    content=msg.content,
                    content_type=msg.content_type,
                    tool_name=msg.tool_name,
                    tool_input=msg.tool_input,
                    tool_output=msg.tool_output,
                    meta_data=msg.meta_data,
                    is_deleted=msg.is_deleted,
                    created_at=msg.created_at,
                    updated_at=msg.updated_at,
                )
                for msg in messages
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation",
        )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    conversation_data: ConversationUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Update a conversation (e.g., change title)."""
    try:
        conversation = await ConversationService.update_conversation(
            db, conversation_id, user.id, conversation_data
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            deleted_at=conversation.deleted_at,
            message_count=0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation",
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete conversation"),
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Delete a conversation (soft delete by default)."""
    try:
        success = await ConversationService.delete_conversation(
            db, conversation_id, user.id, soft_delete=not hard_delete
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )


# -------------------- Message Endpoints --------------------

@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    conversation_id: UUID,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Create a new message in a conversation."""
    try:
        # Ensure conversation_id matches
        message_data.conversation_id = conversation_id
        
        message = await ConversationService.create_message(
            db, message_data, user.id
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            content_type=message.content_type,
            tool_name=message.tool_name,
            tool_input=message.tool_input,
            tool_output=message.tool_output,
            meta_data=message.meta_data,
            is_deleted=message.is_deleted,
            created_at=message.created_at,
            updated_at=message.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create message",
        )


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    skip: int = Query(0, ge=0, description="Number of messages to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum messages to return"),
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Get all messages for a conversation."""
    try:
        messages = await ConversationService.get_conversation_messages(
            db, conversation_id, user.id, skip=skip, limit=limit
        )
        
        return [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                content_type=msg.content_type,
                tool_name=msg.tool_name,
                tool_input=msg.tool_input,
                tool_output=msg.tool_output,
                meta_data=msg.meta_data,
                is_deleted=msg.is_deleted,
                created_at=msg.created_at,
                updated_at=msg.updated_at,
            )
            for msg in messages
        ]
    except Exception as e:
        logger.error(f"Error getting messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages",
        )


@router.patch("/{conversation_id}/messages/{message_id}", response_model=MessageResponse)
async def update_message(
    conversation_id: UUID,
    message_id: UUID,
    message_data: MessageUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Update a message."""
    try:
        message = await ConversationService.update_message(
            db, message_id, conversation_id, user.id, message_data
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            content_type=message.content_type,
            tool_name=message.tool_name,
            tool_input=message.tool_input,
            tool_output=message.tool_output,
            meta_data=message.meta_data,
            is_deleted=message.is_deleted,
            created_at=message.created_at,
            updated_at=message.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message",
        )


# -------------------- Utility Endpoints --------------------

@router.post("/{conversation_id}/generate-title", response_model=ConversationResponse)
async def generate_conversation_title(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Generate a title for a conversation based on its first message."""
    try:
        title = await ConversationService.generate_conversation_title(
            db, conversation_id, user.id
        )
        
        if not title:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or has no messages",
            )
        
        conversation = await ConversationService.get_conversation(
            db, conversation_id, user.id
        )
        
        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            deleted_at=conversation.deleted_at,
            message_count=0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating title: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate title",
        )