import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class UserRole(str, PyEnum):
    """User role for permissions."""
    ADMIN = "admin"
    USER = "user"


class User(SQLAlchemyBaseUserTable[uuid.UUID], Base):
    """User model with UUID primary key and OAuth support."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    role = Column(String, nullable=False, default="user")  # Store as string, validate with Pydantic
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memory_chunks = relationship("MemoryChunk", back_populates="user", cascade="all, delete-orphan")
    web_search_queries = relationship("WebSearchQuery", back_populates="user", cascade="all, delete-orphan")
    gmail_drafts = relationship("GmailDraft", back_populates="user", cascade="all, delete-orphan")
    ai_actions = relationship("AIAction", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class OAuthAccount(Base):
    """OAuth account model for storing Google OAuth tokens."""
    
    __tablename__ = "oauth_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    oauth_name = Column(String, default="google")
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    account_id = Column(String)
    account_email = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="oauth_accounts")
    
    __table_args__ = (
        # Unique constraint on user_id and oauth_name
        {"schema": None},
    )
