"""API routes for Direct Messages."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.user import User
from app.schemas.direct_message import (
    ConversationListResponse,
    ConversationRead,
    DirectMessageCreate,
    DirectMessageRead,
    DirectMessageUpdate,
    MessageListResponse,
    ReactionCreate,
    ReactionSummary,
    UserBasicInfo,
)
from app.services.direct_message_service import direct_message_service

# Import current user dependency
try:
    from app.api.routes.users_complete import get_current_active_user as current_active_user
except ImportError:
    from app.api.routes.auth import current_active_user


router = APIRouter(prefix="/direct-messages", tags=["direct-messages"])


@router.post("/", response_model=DirectMessageRead, status_code=status.HTTP_201_CREATED)
async def send_direct_message(
    message_data: DirectMessageCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Send a direct message to another user.
    
    - **receiver_id**: ID of the user to send message to
    - **content**: Message content
    - **reply_to_id**: Optional ID of message being replied to
    - **attachments**: Optional list of file attachments
    """
    try:
        message = await direct_message_service.send_message(
            session=session,
            sender_id=current_user.id,
            receiver_id=message_data.receiver_id,
            content=message_data.content,
            reply_to_id=message_data.reply_to_id,
            attachments=message_data.attachments
        )
        
        return DirectMessageRead.model_validate(message)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending message: {str(e)}"
        )


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all conversations for the current user.
    
    Returns a list of users the current user has chatted with,
    including the last message and unread count for each conversation.
    """
    try:
        conversations_data = await direct_message_service.get_conversations(
            session=session,
            user_id=current_user.id
        )
        
        conversations = [
            ConversationRead(
                user=UserBasicInfo.model_validate(conv['user']),
                last_message=DirectMessageRead.model_validate(conv['last_message']) if conv['last_message'] else None,
                unread_count=conv['unread_count'],
                last_message_at=conv['last_message_at']
            )
            for conv in conversations_data
        ]
        
        return ConversationListResponse(
            conversations=conversations,
            total=len(conversations)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching conversations: {str(e)}"
        )


@router.get("/with/{user_id}", response_model=MessageListResponse)
async def get_messages_with_user(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get messages between current user and another user.
    
    - **user_id**: ID of the other user
    - **page**: Page number (default: 1)
    - **page_size**: Messages per page (default: 50, max: 100)
    
    Messages are returned in reverse chronological order (newest first).
    Fetching messages automatically marks them as read.
    """
    try:
        other_user_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    try:
        messages, total = await direct_message_service.get_messages(
            session=session,
            user_id=current_user.id,
            other_user_id=other_user_id,
            page=page,
            page_size=page_size
        )
        
        # Process reactions for each message
        message_reads = []
        for message in messages:
            message_read = DirectMessageRead.model_validate(message)
            
            # Get reaction summary
            reactions = await direct_message_service.get_reaction_summary(
                session=session,
                message_id=message.id,
                current_user_id=current_user.id
            )
            message_read.reactions = reactions
            message_reads.append(message_read)
        
        has_more = (page * page_size) < total
        
        return MessageListResponse(
            messages=message_reads,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching messages: {str(e)}"
        )


@router.get("/users", response_model=list[UserBasicInfo])
async def get_eligible_users(
    search: Optional[str] = Query(None, description="Search term for filtering users"),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all non-bot users that can be messaged.
    
    - **search**: Optional search term to filter users by name or email
    
    Returns a list of all active, non-bot users (excluding current user).
    """
    try:
        users = await direct_message_service.get_eligible_users(
            session=session,
            current_user_id=current_user.id,
            search=search
        )
        
        return [UserBasicInfo.model_validate(user) for user in users]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching users: {str(e)}"
        )


@router.patch("/{message_id}", response_model=DirectMessageRead)
async def update_message(
    message_id: str,
    update_data: DirectMessageUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update (edit) a message.
    
    - **message_id**: ID of the message to update
    - **content**: New message content
    
    Only the sender can edit their own messages.
    """
    try:
        msg_id = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID format"
        )
    
    try:
        message = await direct_message_service.update_message(
            session=session,
            message_id=msg_id,
            user_id=current_user.id,
            content=update_data.content
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or unauthorized"
            )
        
        return DirectMessageRead.model_validate(message)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating message: {str(e)}"
        )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete a message (soft delete).
    
    - **message_id**: ID of the message to delete
    
    Only the sender can delete their own messages.
    """
    try:
        msg_id = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID format"
        )
    
    try:
        deleted = await direct_message_service.delete_message(
            session=session,
            message_id=msg_id,
            user_id=current_user.id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or unauthorized"
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting message: {str(e)}"
        )


@router.post("/{message_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_message_as_read(
    message_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Mark a specific message as read.
    
    - **message_id**: ID of the message to mark as read
    
    Only the receiver can mark messages as read.
    """
    try:
        msg_id = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID format"
        )
    
    try:
        marked = await direct_message_service.mark_message_as_read(
            session=session,
            message_id=msg_id,
            user_id=current_user.id
        )
        
        if not marked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or already read"
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking message as read: {str(e)}"
        )


@router.post("/{message_id}/reactions", response_model=list[ReactionSummary], status_code=status.HTTP_201_CREATED)
async def add_reaction(
    message_id: str,
    reaction_data: ReactionCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Add a reaction to a message.
    
    - **message_id**: ID of the message to react to
    - **emoji**: Emoji to react with
    
    Returns updated reaction summary for the message.
    """
    try:
        msg_id = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID format"
        )
    
    try:
        await direct_message_service.add_reaction(
            session=session,
            message_id=msg_id,
            user_id=current_user.id,
            emoji=reaction_data.emoji
        )
        
        # Return updated reaction summary
        reactions = await direct_message_service.get_reaction_summary(
            session=session,
            message_id=msg_id,
            current_user_id=current_user.id
        )
        
        return reactions
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding reaction: {str(e)}"
        )


@router.delete("/{message_id}/reactions/{emoji}", response_model=list[ReactionSummary])
async def remove_reaction(
    message_id: str,
    emoji: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Remove a reaction from a message.
    
    - **message_id**: ID of the message
    - **emoji**: Emoji to remove
    
    Returns updated reaction summary for the message.
    """
    try:
        msg_id = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID format"
        )
    
    try:
        removed = await direct_message_service.remove_reaction(
            session=session,
            message_id=msg_id,
            user_id=current_user.id,
            emoji=emoji
        )
        
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reaction not found"
            )
        
        # Return updated reaction summary
        reactions = await direct_message_service.get_reaction_summary(
            session=session,
            message_id=msg_id,
            current_user_id=current_user.id
        )
        
        return reactions
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing reaction: {str(e)}"
        )
