"""Pydantic schemas for chat operations."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.chat import ChatRoomType, MessageType


# ============================================================================
# Chat Room Schemas
# ============================================================================

class ChatRoomCreate(BaseModel):
    """Schema for creating a new chat room."""
    name: Optional[str] = None
    room_type: ChatRoomType
    description: Optional[str] = None
    member_ids: list[UUID] = Field(default_factory=list, description="Initial members (excluding creator)")


class ChatRoomUpdate(BaseModel):
    """Schema for updating a chat room."""
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None


class ChatRoomMemberRead(BaseModel):
    """Schema for reading chat room member info."""
    id: UUID
    user_id: UUID
    joined_at: datetime
    last_read_at: Optional[datetime] = None
    is_admin: bool
    is_active: bool
    
    # User info (to be populated from join)
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ChatRoomRead(BaseModel):
    """Schema for reading chat room info."""
    id: UUID
    name: Optional[str] = None
    room_type: ChatRoomType
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    
    # Computed fields
    member_count: Optional[int] = None
    unread_count: Optional[int] = None
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChatRoomDetail(ChatRoomRead):
    """Detailed chat room info including members."""
    members: list[ChatRoomMemberRead] = Field(default_factory=list)


# ============================================================================
# Chat Message Schemas
# ============================================================================

class ChatMessageCreate(BaseModel):
    """Schema for creating a new message."""
    room_id: UUID
    message_type: MessageType = MessageType.TEXT
    content: Optional[str] = None
    reply_to_id: Optional[UUID] = None
    forwarded_from_id: Optional[UUID] = None


class ChatMessageUpdate(BaseModel):
    """Schema for updating a message (edit)."""
    content: str


class MessageReadReceiptRead(BaseModel):
    """Schema for reading message read receipt."""
    id: UUID
    user_id: UUID
    read_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageRead(BaseModel):
    """Schema for reading chat message."""
    id: UUID
    room_id: UUID
    sender_id: UUID
    message_type: MessageType
    content: Optional[str] = None
    media_url: Optional[str] = None
    media_filename: Optional[str] = None
    media_size: Optional[int] = None
    media_mime_type: Optional[str] = None
    reply_to_id: Optional[UUID] = None
    forwarded_from_id: Optional[UUID] = None
    is_edited: bool
    edited_at: Optional[datetime] = None
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    
    # Sender info (to be populated from join)
    sender_email: Optional[str] = None
    sender_full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ChatMessageDetail(ChatMessageRead):
    """Detailed message info including read receipts."""
    read_receipts: list[MessageReadReceiptRead] = Field(default_factory=list)


# ============================================================================
# Socket.IO Event Schemas
# ============================================================================

class SocketAuthData(BaseModel):
    """Authentication data for Socket.IO connection."""
    token: str


class JoinRoomData(BaseModel):
    """Data for joining a chat room."""
    room_id: UUID


class LeaveRoomData(BaseModel):
    """Data for leaving a chat room."""
    room_id: UUID


class SendMessageData(BaseModel):
    """Data for sending a message via Socket.IO."""
    room_id: UUID
    message_type: MessageType = MessageType.TEXT
    content: Optional[str] = None
    reply_to_id: Optional[UUID] = None
    forwarded_from_id: Optional[UUID] = None


class EditMessageData(BaseModel):
    """Data for editing a message."""
    message_id: UUID
    content: str


class DeleteMessageData(BaseModel):
    """Data for deleting a message."""
    message_id: UUID


class TypingData(BaseModel):
    """Data for typing indicator."""
    room_id: UUID
    is_typing: bool


class MarkAsReadData(BaseModel):
    """Data for marking messages as read."""
    room_id: UUID
    message_ids: list[UUID] = Field(default_factory=list)


# ============================================================================
# File Upload Schemas
# ============================================================================

class MediaUploadResponse(BaseModel):
    """Response for media upload."""
    url: str
    filename: str
    size: int
    mime_type: str


# ============================================================================
# Pagination Schemas
# ============================================================================

class MessageListResponse(BaseModel):
    """Paginated message list response."""
    messages: list[ChatMessageRead]
    total: int
    page: int
    page_size: int
    has_more: bool


class ChatRoomListResponse(BaseModel):
    """Paginated chat room list response."""
    rooms: list[ChatRoomRead]
    total: int
    page: int
    page_size: int
    has_more: bool
