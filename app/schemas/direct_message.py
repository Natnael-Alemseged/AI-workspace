"""Pydantic schemas for direct messages."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class AttachmentData(BaseModel):
    """Schema for file attachment data."""
    url: str
    filename: str
    size: int
    mime_type: str
    
    class Config:
        extra = "ignore"


class DirectMessageCreate(BaseModel):
    """Schema for creating a new direct message."""
    receiver_id: UUID
    content: str = Field(..., min_length=1)
    reply_to_id: Optional[UUID] = None
    attachments: list[AttachmentData] = Field(default_factory=list)


class DirectMessageUpdate(BaseModel):
    """Schema for updating a message (edit)."""
    content: str = Field(..., min_length=1)


class AttachmentRead(BaseModel):
    """Schema for reading attachment info."""
    id: UUID
    url: str
    filename: str
    size: int
    mime_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReactionRead(BaseModel):
    """Schema for reading reaction info."""
    id: UUID
    user_id: UUID
    emoji: str
    created_at: datetime
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReactionSummary(BaseModel):
    """Summary of reactions grouped by emoji."""
    emoji: str
    count: int
    users: list[UUID]
    user_reacted: bool = False


class DirectMessageRead(BaseModel):
    """Schema for reading direct message."""
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    content: str
    reply_to_id: Optional[UUID] = None
    is_read: bool
    read_at: Optional[datetime] = None
    is_edited: bool
    edited_at: Optional[datetime] = None
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    attachments: list[AttachmentRead] = Field(default_factory=list)
    sender_email: Optional[str] = None
    sender_full_name: Optional[str] = None
    receiver_email: Optional[str] = None
    receiver_full_name: Optional[str] = None
    reactions: list[ReactionSummary] = Field(default_factory=list)
    reaction_count: Optional[int] = 0

    @model_validator(mode='before')
    @classmethod
    def populate_user_info(cls, data):
        """Populate sender and receiver info from relationships."""
        if hasattr(data, 'sender') and data.sender:
            if isinstance(data, dict):
                return data
            result = {
                k: getattr(data, k) 
                for k in ['id', 'sender_id', 'receiver_id', 'content', 'reply_to_id', 
                         'is_read', 'read_at', 'is_edited', 'edited_at', 
                         'is_deleted', 'deleted_at', 'created_at']
            }
            result['attachments'] = data.attachments if hasattr(data, 'attachments') else []
            result['sender_email'] = getattr(data.sender, 'email', None)
            result['sender_full_name'] = getattr(data.sender, 'full_name', None)
            result['receiver_email'] = getattr(data.receiver, 'email', None) if hasattr(data, 'receiver') and data.receiver else None
            result['receiver_full_name'] = getattr(data.receiver, 'full_name', None) if hasattr(data, 'receiver') and data.receiver else None
            result['reaction_count'] = len(data.reactions) if hasattr(data, 'reactions') and data.reactions else 0
            result['reactions'] = []
            return result
        return data

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Response for message list."""
    messages: list[DirectMessageRead]
    total: int
    page: int
    page_size: int
    has_more: bool


class ReactionCreate(BaseModel):
    """Schema for adding a reaction."""
    emoji: str = Field(..., min_length=1, max_length=50)


class UserBasicInfo(BaseModel):
    """Basic user info for conversation list."""
    id: UUID
    email: str
    full_name: Optional[str] = None
    is_online: bool = False
    last_seen_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ConversationRead(BaseModel):
    """Schema for reading conversation info with a user."""
    user: UserBasicInfo
    last_message: Optional[DirectMessageRead] = None
    unread_count: int = 0
    last_message_at: Optional[datetime] = None


class ConversationListResponse(BaseModel):
    """Response for conversation list."""
    conversations: list[ConversationRead]
    total: int
