"""Chat models for real-time messaging."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

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


class ChatRoomType(str, PyEnum):
    """Type of chat room."""
    DIRECT = "direct"  # 1-on-1 chat
    GROUP = "group"    # Group chat


class MessageType(str, PyEnum):
    """Type of message content."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"


class ChatRoom(Base):
    """Chat room model for both 1-1 and group chats."""
    
    __tablename__ = "chat_rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)  # Optional for direct chats, required for groups
    room_type = Column(Enum(ChatRoomType), nullable=False, default=ChatRoomType.DIRECT)
    description = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)  # Supabase storage URL
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("ChatRoomMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")


class ChatRoomMember(Base):
    """Members of a chat room."""
    
    __tablename__ = "chat_room_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_read_at = Column(DateTime(timezone=True), nullable=True)  # For unread message tracking
    is_admin = Column(Boolean, default=False, nullable=False)  # For group chat admins
    is_active = Column(Boolean, default=True, nullable=False)  # For soft deletion
    
    # Relationships
    room = relationship("ChatRoom", back_populates="members")
    user = relationship("User")


class ChatMessage(Base):
    """Chat messages with support for text and media."""
    
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id"), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)  # Nullable for AI messages
    message_type = Column(Enum(MessageType), nullable=False, default=MessageType.TEXT)
    content = Column(Text, nullable=True)  # Text content or media description
    media_url = Column(String, nullable=True)  # Supabase storage URL for media
    media_filename = Column(String, nullable=True)  # Original filename
    media_size = Column(Integer, nullable=True)  # File size in bytes
    media_mime_type = Column(String, nullable=True)  # MIME type
    
    # Reply and forward functionality
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=True, index=True)
    forwarded_from_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=True, index=True)
    
    # Edit and delete tracking
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    reply_to = relationship("ChatMessage", remote_side=[id], foreign_keys=[reply_to_id])
    forwarded_from = relationship("ChatMessage", remote_side=[id], foreign_keys=[forwarded_from_id])
    read_receipts = relationship("MessageReadReceipt", back_populates="message", cascade="all, delete-orphan")


class MessageReadReceipt(Base):
    """Track message read status for each user."""
    
    __tablename__ = "message_read_receipts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("ChatMessage", back_populates="read_receipts")
    user = relationship("User")
