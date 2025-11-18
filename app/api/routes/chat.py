"""Chat API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.users_complete import get_current_user
from app.core.logging import logger
from app.db import get_async_session
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageDetail,
    ChatMessageRead,
    ChatMessageUpdate,
    ChatRoomCreate,
    ChatRoomDetail,
    ChatRoomListResponse,
    ChatRoomRead,
    ChatRoomUpdate,
    MarkAsReadData,
    MediaUploadResponse,
    MessageListResponse,
)
from app.services.chat import ChatService
from app.services.socketio_service import emit_to_room
from app.services.integrations import SupabaseService

router = APIRouter(prefix="/chat", tags=["chat"])


# ============================================================================
# Chat Room Endpoints
# ============================================================================

@router.post("/rooms", response_model=ChatRoomDetail, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: ChatRoomCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new chat room."""
    try:
        room = await ChatService.create_room(session, room_data, current_user.id)
        
        # Notify members via Socket.IO
        await emit_to_room(
            str(room.id),
            "room_created",
            {
                "room_id": str(room.id),
                "room_type": room.room_type.value,
                "created_by": str(current_user.id)
            }
        )
        
        return room
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create room"
        )


@router.get("/rooms", response_model=ChatRoomListResponse)
async def get_user_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all chat rooms for the current user."""
    try:
        rooms, total = await ChatService.get_user_rooms(
            session, current_user.id, page, page_size
        )
        
        has_more = (page * page_size) < total
        
        return ChatRoomListResponse(
            rooms=rooms,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error getting user rooms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rooms"
        )


@router.get("/rooms/{room_id}", response_model=ChatRoomDetail)
async def get_room(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific chat room."""
    try:
        room = await ChatService.get_room_by_id(session, room_id, current_user.id)
        
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )
        
        return room
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get room"
        )


@router.patch("/rooms/{room_id}", response_model=ChatRoomRead)
async def update_room(
    room_id: UUID,
    room_data: ChatRoomUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update a chat room (admin only)."""
    try:
        room = await ChatService.update_room(
            session, room_id, current_user.id, room_data
        )
        
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )
        
        # Notify room members
        await emit_to_room(
            str(room_id),
            "room_updated",
            {
                "room_id": str(room_id),
                "updated_by": str(current_user.id)
            }
        )
        
        return room
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update room"
        )


@router.post("/rooms/{room_id}/members/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_member(
    room_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Add a member to a chat room (admin only)."""
    try:
        member = await ChatService.add_member(
            session, room_id, current_user.id, user_id
        )
        
        # Notify room members
        await emit_to_room(
            str(room_id),
            "member_added",
            {
                "room_id": str(room_id),
                "user_id": str(user_id),
                "added_by": str(current_user.id)
            }
        )
        
        return {"message": "Member added successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add member"
        )


@router.delete("/rooms/{room_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    room_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove a member from a chat room (admin or self)."""
    try:
        success = await ChatService.remove_member(
            session, room_id, current_user.id, user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Notify room members
        await emit_to_room(
            str(room_id),
            "member_removed",
            {
                "room_id": str(room_id),
                "user_id": str(user_id),
                "removed_by": str(current_user.id)
            }
        )
        
        return None
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member"
        )


# ============================================================================
# Message Endpoints
# ============================================================================

@router.post("/messages", response_model=ChatMessageRead, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new message."""
    try:
        message = await ChatService.create_message(
            session, message_data, current_user.id
        )
        
        # Notify room members via Socket.IO
        await emit_to_room(
            str(message.room_id),
            "new_message",
            {
                "room_id": str(message.room_id),
                "message": {
                    "id": str(message.id),
                    "sender_id": str(message.sender_id),
                    "content": message.content,
                    "message_type": message.message_type.value,
                    "created_at": message.created_at.isoformat(),
                    "reply_to_id": str(message.reply_to_id) if message.reply_to_id else None,
                    "forwarded_from_id": str(message.forwarded_from_id) if message.forwarded_from_id else None
                }
            }
        )
        
        return message
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create message"
        )


@router.get("/rooms/{room_id}/messages", response_model=MessageListResponse)
async def get_room_messages(
    room_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get messages for a chat room."""
    try:
        messages, total = await ChatService.get_room_messages(
            session, room_id, current_user.id, page, page_size
        )
        
        has_more = (page * page_size) < total
        
        return MessageListResponse(
            messages=messages,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )


@router.patch("/messages/{message_id}", response_model=ChatMessageRead)
async def update_message(
    message_id: UUID,
    message_data: ChatMessageUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update (edit) a message."""
    try:
        message = await ChatService.update_message(
            session, message_id, current_user.id, message_data.content
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Notify room members
        await emit_to_room(
            str(message.room_id),
            "message_edited",
            {
                "room_id": str(message.room_id),
                "message_id": str(message_id),
                "content": message.content,
                "edited_by": str(current_user.id)
            }
        )
        
        return message
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message"
        )


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a message."""
    try:
        # Get message first to get room_id
        from sqlalchemy import select
        from app.models.chat import ChatMessage
        
        query = select(ChatMessage).where(ChatMessage.id == message_id)
        result = await session.execute(query)
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        room_id = message.room_id
        
        success = await ChatService.delete_message(
            session, message_id, current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Notify room members
        await emit_to_room(
            str(room_id),
            "message_deleted",
            {
                "room_id": str(room_id),
                "message_id": str(message_id),
                "deleted_by": str(current_user.id)
            }
        )
        
        return None
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        )


@router.post("/rooms/{room_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_messages_as_read(
    room_id: UUID,
    data: MarkAsReadData,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Mark messages as read."""
    try:
        await ChatService.mark_messages_as_read(
            session, room_id, current_user.id, data.message_ids
        )
        
        # Notify room members
        await emit_to_room(
            str(room_id),
            "messages_read",
            {
                "room_id": str(room_id),
                "user_id": str(current_user.id),
                "message_ids": [str(mid) for mid in data.message_ids]
            },
            exclude_user=str(current_user.id)
        )
        
        return None
        
    except Exception as e:
        logger.error(f"Error marking messages as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark messages as read"
        )


# ============================================================================
# Media Upload Endpoints
# ============================================================================

@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload media file to Supabase storage."""
    try:
        # Read file content
        content = await file.read()
        
        # Upload to Supabase
        result = await SupabaseService.upload_file(
            file_content=content,
            filename=file.filename,
            content_type=file.content_type,
            folder=f"chat/{current_user.id}"
        )
        
        return MediaUploadResponse(
            url=result["url"],
            filename=result["filename"],
            size=result["size"],
            mime_type=result["content_type"]
        )
        
    except Exception as e:
        logger.error(f"Error uploading media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload media"
        )


@router.get("/upload/signed-url")
async def get_signed_upload_url(
    filename: str = Query(...),
    current_user: User = Depends(get_current_user)
):
    """Get a signed URL for direct client-side upload."""
    try:
        result = await SupabaseService.get_signed_upload_url(
            filename=filename,
            folder=f"chat/{current_user.id}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating signed upload URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate signed upload URL"
        )
