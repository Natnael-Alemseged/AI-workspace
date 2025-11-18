import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db import Base


class WebSearchEngine(str, enum.Enum):
    """Web search engine enum."""
    BING = "bing"
    SERPAPI = "serpapi"


class WebSearchQuery(Base):
    """Web search query model for storing search results."""
    
    __tablename__ = "web_search_queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    query = Column(Text, nullable=False, index=True)
    engine = Column(Enum(WebSearchEngine, name="enum_web_search_engine"), default=WebSearchEngine.BING, index=True)
    raw_results = Column(JSONB, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="web_search_queries")
    message = relationship("Message", back_populates="web_search_queries")