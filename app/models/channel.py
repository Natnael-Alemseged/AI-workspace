"""Channel and Topic models for organized team communication."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class Channel(Base):
    """Channel model for organizing topics (e.g., Design, Development)."""
    
    __tablename__ = "channels"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Emoji or icon identifier
    color = Column(String(7), nullable=True)  # Hex color code
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    topics = relationship("Topic", back_populates="channel", cascade="all, delete-orphan")


class Topic(Base):
    """Topic model for discussions within a channel."""
    
    __tablename__ = "topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    channel = relationship("Channel", back_populates="topics")
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("TopicMember", back_populates="topic", cascade="all, delete-orphan")
    messages = relationship("TopicMessage", back_populates="topic", cascade="all, delete-orphan")


class TopicMember(Base):
    """Members of a topic with role-based permissions."""
    
    __tablename__ = "topic_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    topic = relationship("Topic", back_populates="members")
    user = relationship("User")


class TopicMessage(Base):
    """Messages within topics with mentions and reactions."""
    
    __tablename__ = "topic_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)  # Nullable for AI messages
    content = Column(Text, nullable=False)
    
    # Reply functionality
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("topic_messages.id"), nullable=True, index=True)
    
    # Edit and delete tracking
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    topic = relationship("Topic", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    reply_to = relationship("TopicMessage", remote_side=[id], foreign_keys=[reply_to_id])
    mentions = relationship("MessageMention", back_populates="message", cascade="all, delete-orphan")
    reactions = relationship("MessageReaction", back_populates="message", cascade="all, delete-orphan")


class MessageMention(Base):
    """Track user mentions in messages."""
    
    __tablename__ = "message_mentions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("topic_messages.id"), nullable=False, index=True)
    mentioned_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    message = relationship("TopicMessage", back_populates="mentions")
    mentioned_user = relationship("User")


class MessageReaction(Base):
    """Reactions to messages (emoji reactions)."""
    
    __tablename__ = "message_reactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("topic_messages.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    emoji = Column(String(50), nullable=False)  # Emoji unicode or shortcode
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("TopicMessage", back_populates="reactions")
    user = relationship("User")
