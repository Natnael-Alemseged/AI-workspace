import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db import Base


class AIActionType(str, enum.Enum):
    """AI action type enum."""
    WEB_SEARCH = "web_search"
    EMAIL_DRAFT = "email_draft"
    EMAIL_SEND = "email_send"
    OTHER_TOOL = "other_tool"


class AIActionStatus(str, enum.Enum):
    """AI action status enum."""
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"


class AIAction(Base):
    """AI action model for tracking AI-initiated actions."""
    
    __tablename__ = "ai_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True, index=True)
    action_type = Column(Enum(AIActionType, name="enum_ai_action_type"), nullable=False, index=True)
    action_payload = Column(JSONB, nullable=False)
    status = Column(Enum(AIActionStatus, name="enum_ai_action_status"), default=AIActionStatus.PENDING, index=True)
    result = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="ai_actions")
    conversation = relationship("Conversation", back_populates="ai_actions")
    message = relationship("Message", back_populates="ai_actions")