"""Pydantic schemas for channels and topics."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field, model_validator


# ============================================================================
# Channel Schemas
# ============================================================================

class ChannelCreate(BaseModel):
    """Schema for creating a new channel (admin only)."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class ChannelUpdate(BaseModel):
    """Schema for updating a channel (admin only)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class ChannelRead(BaseModel):
    """Schema for reading channel info."""
    id: UUID
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    
    # Computed fields
    topic_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ChannelListResponse(BaseModel):
    """Response for channel list."""
    channels: list[ChannelRead]
    total: int


# ============================================================================
# Topic Schemas
# ============================================================================

class TopicCreate(BaseModel):
    """Schema for creating a new topic (admin only)."""
    channel_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    member_ids: list[UUID] = Field(default_factory=list, description="Initial members to add")


class TopicUpdate(BaseModel):
    """Schema for updating a topic (admin only)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_pinned: Optional[bool] = None


class TopicMemberRead(BaseModel):
    """Schema for reading topic member info."""
    id: UUID
    user_id: UUID
    joined_at: datetime
    last_read_at: Optional[datetime] = None
    is_active: bool
    
    # User info (populated from join)
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    
    @model_validator(mode='before')
    @classmethod
    def populate_user_info(cls, data):
        """Populate user info from the user relationship."""
        if hasattr(data, 'user') and data.user:
            if isinstance(data, dict):
                return data
            # Extract user info from ORM relationship
            return {
                **{k: getattr(data, k) for k in ['id', 'user_id', 'joined_at', 'last_read_at', 'is_active']},
                'user_email': getattr(data.user, 'email', None),
                'user_full_name': getattr(data.user, 'full_name', None),
            }
        return data
    
    class Config:
        from_attributes = True


class UserForTopicAddition(BaseModel):
    """Schema for users that can be added to a topic."""
    id: UUID
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_member: bool  # True if already a member of the topic
    
    class Config:
        from_attributes = True


class TopicRead(BaseModel):
    """Schema for reading topic info."""
    id: UUID
    channel_id: UUID
    name: str
    description: Optional[str] = None
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    is_pinned: bool
    
    # Computed fields
    member_count: Optional[int] = 0
    message_count: Optional[int] = 0
    unread_count: Optional[int] = 0
    last_message_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TopicDetail(TopicRead):
    """Detailed topic info including members."""
    members: list[TopicMemberRead] = Field(default_factory=list)
    channel_name: Optional[str] = None


class TopicListResponse(BaseModel):
    """Response for topic list."""
    topics: list[TopicRead]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# Topic Message Schemas
# ============================================================================

class AttachmentData(BaseModel):
    """Schema for file attachment data."""
    url: str
    filename: str
    size: int
    mime_type: str
    
    class Config:
        extra = "ignore"  # Ignore extra fields like 'id' and 'created_at' from frontend


class TopicMessageCreate(BaseModel):
    """Schema for creating a new message in a topic."""
    content: str = Field(..., min_length=1)
    reply_to_id: Optional[UUID] = None
    mentioned_user_ids: list[UUID] = Field(default_factory=list, description="Users to mention")
    attachments: list[AttachmentData] = Field(default_factory=list, description="File attachments")


class TopicMessageUpdate(BaseModel):
    """Schema for updating a message (edit)."""
    content: str = Field(..., min_length=1)


class MentionRead(BaseModel):
    """Schema for reading mention info."""
    id: UUID
    mentioned_user_id: UUID
    created_at: datetime
    is_read: bool
    
    # User info
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReactionRead(BaseModel):
    """Schema for reading reaction info."""
    id: UUID
    user_id: UUID
    emoji: str
    created_at: datetime
    
    # User info
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReactionSummary(BaseModel):
    """Summary of reactions grouped by emoji."""
    emoji: str
    count: int
    users: list[UUID]
    user_reacted: bool = False  # Whether current user reacted


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


class TopicMessageRead(BaseModel):
    """Schema for reading topic message."""
    id: UUID
    topic_id: UUID
    sender_id: UUID
    content: str
    reply_to_id: Optional[UUID] = None
    is_edited: bool
    edited_at: Optional[datetime] = None
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime

    # Attachments
    attachments: list[AttachmentRead] = Field(default_factory=list)

    # Sender info
    sender_email: Optional[str] = None
    sender_full_name: Optional[str] = None

    # Counts
    mention_count: Optional[int] = 0
    reaction_count: Optional[int] = 0

    # Reactions
    reactions: list[ReactionSummary] = Field(default_factory=list)

    # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
    class Config:
        from_attributes = True
    # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

class TopicMessageDetail(TopicMessageRead):
    """Detailed message info including mentions (reactions inherited from TopicMessageRead)."""
    mentions: list[MentionRead] = Field(default_factory=list)
    reply_to_content: Optional[str] = None  # Content of replied message


class MessageListResponse(BaseModel):
    messages: list[TopicMessageRead]   # ← must be TopicMessageRead, not raw model
    total: int
    page: int
    page_size: int
    has_more: bool

    class Config:
        from_attributes = True  # optional, but safe
# ============================================================================
# Reaction Schemas
# ============================================================================

class ReactionCreate(BaseModel):
    """Schema for adding a reaction."""
    emoji: str = Field(..., min_length=1, max_length=50)


# ============================================================================
# Socket.IO Event Schemas
# ============================================================================

class JoinTopicData(BaseModel):
    """Data for joining a topic."""
    topic_id: UUID


class LeaveTopicData(BaseModel):
    """Data for leaving a topic."""
    topic_id: UUID


class TypingData(BaseModel):
    """Data for typing indicator."""
    topic_id: UUID
    is_typing: bool
