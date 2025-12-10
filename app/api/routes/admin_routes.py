"""Admin routes for user management."""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.users_complete import get_current_user
from app.core.logging import logger
from app.db import get_async_session
from app.models.user import User, UserRole
from app.schemas.user import AdminUserRead, PendingUserRead, UserRead

router = APIRouter()


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify current user is an admin or superuser."""
    if current_user.role != UserRole.ADMIN and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify current user is a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required"
        )
    return current_user


@router.get("/users/pending", response_model=List[PendingUserRead])
async def get_pending_users(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all pending users (inactive and not approved).
    Requires admin or superuser privileges.
    """
    try:
        query = select(User).where(
            and_(
                User.is_active == False,
                User.is_approved == False,
                User.is_bot == False  # Exclude bots
            )
        ).order_by(User.created_at.desc())
        
        result = await session.execute(query)
        users = result.scalars().all()
        
        # Build response with registration method
        pending_users = []
        for user in users:
            # Determine registration method: OAuth users have empty hashed_password
            registration_method = "oauth" if (user.hashed_password == "" or user.hashed_password is None) else "email"
            
            pending_users.append(PendingUserRead(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                created_at=user.created_at,
                is_verified=user.is_verified,
                registration_method=registration_method
            ))
        
        logger.info(f"Admin {current_user.id} fetched {len(pending_users)} pending users")
        return pending_users
        
    except Exception as e:
        logger.error(f"Error fetching pending users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pending users"
        )



@router.patch("/users/{user_id}/approve", response_model=UserRead)
async def approve_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Approve a pending user.
    Sets is_active=True, is_approved=True, and role="admin".
    Requires admin or superuser privileges.
    """
    try:
        # Get the user to approve
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already approved"
            )
        
        # Approve the user
        user.is_active = True
        user.is_approved = True
        user.is_superuser=True
        user.role = "admin"  # Grant admin role for channel/topic CRUD
        
        await session.commit()
        await session.refresh(user)
        
        logger.info(f"Admin {current_user.id} approved user {user_id}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error approving user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve user"
        )


@router.patch("/users/{user_id}/promote", response_model=UserRead)
async def promote_user_to_superuser(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Promote an admin user to superuser.
    Sets is_superuser=True.
    Requires superuser privileges.
    """
    try:
        # Get the user to promote
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a superuser"
            )
        
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must be an admin before being promoted to superuser"
            )
        
        # Promote to superuser
        user.is_superuser = True
        
        await session.commit()
        await session.refresh(user)
        
        logger.info(f"Superuser {current_user.id} promoted user {user_id} to superuser")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error promoting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to promote user"
        )


@router.get("/users", response_model=List[AdminUserRead])
async def get_all_users(
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, active, all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all users with optional filtering.
    Requires admin or superuser privileges.
    """
    try:
        # Build query based on filter
        conditions = [User.is_bot == False]  # Exclude bots
        
        if status_filter == "pending":
            conditions.append(User.is_approved == False)
        elif status_filter == "active":
            conditions.append(User.is_approved == True)
        # "all" or None - no additional filter
        
        query = select(User).where(
            and_(*conditions)
        ).order_by(User.created_at.desc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await session.execute(query)
        users = result.scalars().all()
        
        logger.info(f"Admin {current_user.id} fetched {len(users)} users with filter: {status_filter}")
        return [AdminUserRead(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_approved=user.is_approved,
            is_verified=user.is_verified,
            created_at=user.created_at
        ) for user in users]
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )
