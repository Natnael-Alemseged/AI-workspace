import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db import Base


class MessageRole(str, enum.Enum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ContentType(str, enum.Enum):
    """Content type enum."""
    TEXT = "text"
    MARKDOWN = "markdown"
    CODE = "code"


class Message(Base):
    """Message model for storing conversation messages."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(Enum(MessageRole, name="enum_message_role"), nullable=False, index=True)
    content = Column(Text, nullable=True)
    content_type = Column(Enum(ContentType, name="enum_content_type"), default=ContentType.TEXT)
    tool_name = Column(String, nullable=True, index=True)
    tool_input = Column(JSONB, nullable=True)
    tool_output = Column(JSONB, nullable=True)
    meta_data = Column("metadata", JSONB, default={})
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    memory_chunks = relationship("MemoryChunk", back_populates="message", cascade="all, delete-orphan")
    web_search_queries = relationship("WebSearchQuery", back_populates="message", cascade="all, delete-orphan")
    citations = relationship("MessageCitation", back_populates="message", cascade="all, delete-orphan")
    gmail_drafts = relationship("GmailDraft", back_populates="message", cascade="all, delete-orphan")
    ai_actions = relationship("AIAction", back_populates="message", cascade="all, delete-orphan")


class MessageCitation(Base):
    """Citation model for storing web search sources."""
    
    __tablename__ = "message_citations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True)
    source_url = Column(Text, nullable=False, index=True)
    title = Column(String, nullable=True)
    snippet = Column(Text, nullable=True)
    rank = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("Message", back_populates="citations")