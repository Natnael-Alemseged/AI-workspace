"""Direct Message models for one-to-one private conversations."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base

"""Direct message model for private one-to-one conversations."""
class DirectMessage(Base):

    
    __tablename__ = "direct_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # Reply functionality
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("direct_messages.id"), nullable=True, index=True)
    
    # Read/unread tracking
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Edit and delete tracking
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    reply_to = relationship("DirectMessage", remote_side=[id], foreign_keys=[reply_to_id])
    reactions = relationship("DirectMessageReaction", back_populates="message", cascade="all, delete-orphan")
    attachments = relationship("DirectMessageAttachment", back_populates="message", cascade="all, delete-orphan")


class DirectMessageReaction(Base):
    """Reactions to direct messages (emoji reactions)."""
    
    __tablename__ = "direct_message_reactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("direct_messages.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    emoji = Column(String(50), nullable=False)  # Emoji unicode or shortcode
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("DirectMessage", back_populates="reactions")
    user = relationship("User")


class DirectMessageAttachment(Base):
    """File attachments for direct messages."""
    
    __tablename__ = "direct_message_attachments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("direct_messages.id"), nullable=False, index=True)
    url = Column(String, nullable=False)  # Supabase storage URL
    filename = Column(String, nullable=False)  # Original filename
    size = Column(Integer, nullable=False)  # File size in bytes
    mime_type = Column(String, nullable=False)  # MIME type
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("DirectMessage", back_populates="attachments")
