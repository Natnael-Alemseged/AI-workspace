from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.message import ContentType, MessageRole


# -------------------- Message Schemas --------------------

class MessageBase(BaseModel):
    """Base message schema."""
    role: MessageRole
    content: Optional[str] = None
    content_type: ContentType = ContentType.TEXT
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[dict] = None
    meta_data: Optional[dict] = Field(default_factory=dict)


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    conversation_id: UUID


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    content: Optional[str] = None
    content_type: Optional[ContentType] = None
    tool_output: Optional[dict] = None
    meta_data: Optional[dict] = None
    is_deleted: Optional[bool] = None


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: UUID
    conversation_id: UUID
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -------------------- Conversation Schemas --------------------

class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = None
    deleted_at: Optional[datetime] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation response without messages."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Schema for conversation response with messages."""
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list."""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# -------------------- Chat Request/Response Schemas --------------------

class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str
    conversation_id: Optional[UUID] = None
    agent_type: Optional[str] = "general"  # gmail, calendar, search, weather, drive, general


class ChatResponse(BaseModel):
    """Schema for chat response."""
    conversation_id: UUID
    message_id: UUID
    role: MessageRole
    content: str
    content_type: ContentType = ContentType.TEXT
    tool_calls_executed: Optional[List[dict]] = []
    created_at: datetime