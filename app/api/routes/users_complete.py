"""User management endpoints and authentication helpers."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from jose import JWTError, jwt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import SECRET_KEY, ALGORITHM
from app.db import get_async_session
from app.models.user import User
from app.models.chat import ChatRoom, ChatRoomMember, ChatMessage, MessageReadReceipt, ChatRoomType
from app.schemas.user import UserRead, UserUpdate, UserListResponse, UserListItem, LastMessageInfo
from app.schemas.token import TokenData

router = APIRouter()


async def get_current_user(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """Get current user from JWT token in Authorization header."""
    from app.core.logging import logger
    
    if not authorization:
        logger.error("No Authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.error("Invalid Authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    try:
        payload = jwt.decode(
            token,
            str(SECRET_KEY),
            algorithms=[ALGORITHM],
            audience="fastapi-users:auth"
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"Token decoded, user_id: {user_id}")
        
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user
    result = await session.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"User authenticated: {user.id}")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return current_user


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update current user information."""
    from app.core.logging import logger
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await session.commit()
    await session.refresh(current_user)
    
    logger.info(f"User {current_user.id} updated their profile")
    
    return current_user


@router.get("/users", response_model=UserListResponse)
async def get_all_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all users for chat selection with last message and unread count.
    
    Returns a paginated list of active users excluding the current user.
    Includes last message from direct chat and unread message count.
    Supports optional search by email or full name.
    """
    from app.core.logging import logger
    from sqlalchemy.orm import aliased
    
    try:
        # Base query - exclude current user and only show active users
        query = select(User).where(
            User.id != current_user.id,
            User.is_active == True
        )
        
        # Add search filter if provided
        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(
                (func.lower(User.email).like(search_term)) |
                (func.lower(User.full_name).like(search_term))
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(User.email).offset((page - 1) * page_size).limit(page_size)
        
        # Execute query
        result = await session.execute(query)
        users = result.scalars().all()
        
        # Build user items with chat metadata
        user_items = []
        
        for user in users:
            # Find direct chat room between current user and this user
            room_query = select(ChatRoom).join(
                ChatRoomMember, ChatRoom.id == ChatRoomMember.room_id
            ).where(
                ChatRoom.room_type == ChatRoomType.DIRECT,
                ChatRoomMember.user_id.in_([current_user.id, user.id]),
                ChatRoomMember.is_active == True
            ).group_by(ChatRoom.id).having(
                func.count(ChatRoomMember.user_id) == 2
            )
            
            room_result = await session.execute(room_query)
            room = room_result.scalar_one_or_none()
            
            last_message_info = None
            unread_count = 0
            room_id = None
            
            if room:
                room_id = room.id
                
                # Get last message in this room
                last_msg_query = select(ChatMessage).where(
                    ChatMessage.room_id == room.id,
                    ChatMessage.deleted_at.is_(None)
                ).order_by(ChatMessage.created_at.desc()).limit(1)
                
                last_msg_result = await session.execute(last_msg_query)
                last_message = last_msg_result.scalar_one_or_none()
                
                if last_message:
                    last_message_info = LastMessageInfo(
                        content=last_message.content,
                        created_at=last_message.created_at.isoformat(),
                        sender_id=last_message.sender_id,
                        message_type=last_message.message_type.value
                    )
                
                # Get unread count - messages sent by other user that current user hasn't read
                unread_query = select(func.count(ChatMessage.id)).where(
                    ChatMessage.room_id == room.id,
                    ChatMessage.sender_id == user.id,
                    ChatMessage.deleted_at.is_(None),
                    ~ChatMessage.id.in_(
                        select(MessageReadReceipt.message_id).where(
                            MessageReadReceipt.user_id == current_user.id
                        )
                    )
                )
                
                unread_result = await session.execute(unread_query)
                unread_count = unread_result.scalar() or 0
            
            user_items.append(
                UserListItem(
                    id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    is_active=user.is_active,
                    last_message=last_message_info,
                    unread_count=unread_count,
                    room_id=room_id
                )
            )
        
        has_more = (page * page_size) < total
        
        logger.info(f"User {current_user.id} fetched {len(user_items)} users (page {page})")
        
        return UserListResponse(
            users=user_items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )