import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db import Base


class GmailDraftStatus(str, enum.Enum):
    """Gmail draft status enum."""
    DRAFT = "draft"
    SENT = "sent"
    FAILED = "failed"


class GmailDraft(Base):
    """Gmail draft model for storing email drafts and sent emails."""
    
    __tablename__ = "gmail_drafts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    thread_id = Column(String, nullable=True)
    message_id_gmail = Column(String, nullable=True, index=True)
    to_recipients = Column(JSONB, nullable=True)
    cc_recipients = Column(JSONB, nullable=True)
    bcc_recipients = Column(JSONB, nullable=True)
    subject = Column(String, nullable=True)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    in_reply_to = Column(String, nullable=True)
    status = Column(Enum(GmailDraftStatus, name="enum_gmail_draft_status"), default=GmailDraftStatus.DRAFT, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    gmail_response = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="gmail_drafts")
    message = relationship("Message", back_populates="gmail_drafts")
    attachments = relationship("EmailAttachment", back_populates="gmail_draft", cascade="all, delete-orphan")


class EmailAttachment(Base):
    """Email attachment model for storing file metadata."""
    
    __tablename__ = "email_attachments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gmail_draft_id = Column(UUID(as_uuid=True), ForeignKey("gmail_drafts.id"), nullable=False, index=True)
    filename = Column(String, nullable=False, index=True)
    mime_type = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    storage_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    gmail_draft = relationship("GmailDraft", back_populates="attachments")