import uuid
from typing import List, Optional

from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole


class UserRead(schemas.BaseUser[uuid.UUID]):
    model_config = ConfigDict(use_enum_values=True)
    
    full_name: Optional[str] = None
    role: UserRole


class UserCreate(schemas.BaseUserCreate):
    full_name: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    password: Optional[str] = None
    full_name: Optional[str] = None


class LastMessageInfo(BaseModel):
    """Last message information."""
    content: str
    created_at: str
    sender_id: uuid.UUID
    message_type: str
    
    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    """Simplified user info for listing with chat metadata."""
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    is_active: bool
    last_message: Optional[LastMessageInfo] = None
    unread_count: int = 0
    room_id: Optional[uuid.UUID] = None  # Direct chat room ID if exists
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Response for user list endpoint."""
    users: List[UserListItem]
    total: int
    page: int
    page_size: int
    has_more: bool
