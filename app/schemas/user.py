import uuid
from typing import List, Optional
from datetime import datetime

from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole


class UserRead(schemas.BaseUser[uuid.UUID]):
    model_config = ConfigDict(use_enum_values=True)
    
    full_name: Optional[str] = None
    role: UserRole
    is_approved: bool


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


# Admin-specific schemas
class PendingUserRead(BaseModel):
    """Schema for pending user information."""
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    created_at: datetime
    is_verified: bool
    registration_method: str  # "email" or "oauth"
    
    class Config:
        from_attributes = True


class UserApprovalUpdate(BaseModel):
    """Schema for approving a user."""
    pass  # No body needed, approval is triggered by endpoint


class UserPromoteUpdate(BaseModel):
    """Schema for promoting a user to superuser."""
    pass  # No body needed, promotion is triggered by endpoint


class AdminUserRead(BaseModel):
    """Schema for admin user listing."""
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_superuser: bool
    is_approved: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
