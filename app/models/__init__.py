"""Database models for Armada Den."""

from app.models.ai_action import AIAction, AIActionStatus, AIActionType
from app.models.audit import AuditLog
from app.models.channel import (
    Channel,
    MessageMention,
    MessageReaction,
    Topic,
    TopicMember,
    TopicMessage,
)
from app.models.chat import (
    ChatMessage,
    ChatRoom,
    ChatRoomMember,
    ChatRoomType,
    MessageReadReceipt,
    MessageType,
)
from app.models.conversation import Conversation
from app.models.gmail import EmailAttachment, GmailDraft, GmailDraftStatus
from app.models.memory import MemoryChunk, SourceType
from app.models.message import ContentType, Message, MessageCitation, MessageRole
from app.models.user import OAuthAccount, PushSubscription, User, UserRole
from app.models.web_search import WebSearchEngine, WebSearchQuery

__all__ = [
    # User models
    "User",
    "UserRole",
    "OAuthAccount",
    "PushSubscription",
    # Conversation models
    "Conversation",
    "Message",
    "MessageRole",
    "ContentType",
    "MessageCitation",
    # Memory models
    "MemoryChunk",
    "SourceType",
    # Web search models
    "WebSearchQuery",
    "WebSearchEngine",
    # Gmail models
    "GmailDraft",
    "GmailDraftStatus",
    "EmailAttachment",
    # AI action models
    "AIAction",
    "AIActionType",
    "AIActionStatus",
    # Audit models
    "AuditLog",
    # Chat models
    "ChatRoom",
    "ChatRoomType",
    "ChatRoomMember",
    "ChatMessage",
    "MessageType",
    "MessageReadReceipt",
    # Channel/Topic models
    "Channel",
    "Topic",
    "TopicMember",
    "TopicMessage",
    "MessageMention",
    "MessageReaction",
]