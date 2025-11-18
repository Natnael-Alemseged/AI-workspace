import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db import Base


class SourceType(str, enum.Enum):
    """Source type enum for memory chunks."""
    CONVERSATION = "conversation"
    EMAIL = "email"
    WEB_SEARCH = "web_search"
    CUSTOM = "custom"


class MemoryChunk(Base):
    """Memory chunk model for RAG (Retrieval-Augmented Generation)."""
    
    __tablename__ = "memory_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    embedding_vector_id = Column(String, nullable=True)  # External ID in Pinecone/Supermemory
    meta_data = Column("metadata", JSONB, default={})
    source_type = Column(Enum(SourceType, name="enum_source_type"), default=SourceType.CONVERSATION, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="memory_chunks")
    conversation = relationship("Conversation", back_populates="memory_chunks")
    message = relationship("Message", back_populates="memory_chunks")