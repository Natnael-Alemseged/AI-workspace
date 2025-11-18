"""Permission decorators and utilities."""
from functools import wraps
from typing import Callable

from fastapi import HTTPException, status

from app.models.user import User, UserRole


def require_admin(func: Callable) -> Callable:
    """
    Decorator to require admin role for an endpoint.
    
    Usage:
        @router.get("/admin-only")
        @require_admin
        async def admin_endpoint(current_user: User = Depends(get_current_user)):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find current_user in kwargs
        current_user = kwargs.get('current_user')
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if current_user.role != UserRole.ADMIN and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


def is_admin(user: User) -> bool:
    """Check if user is an admin."""
    return user.role == UserRole.ADMIN or user.is_superuser


def is_user(user: User) -> bool:
    """Check if user is a regular user."""
    return user.role == UserRole.USER


def check_permission(user: User, required_role: UserRole) -> bool:
    """
    Check if user has the required role.
    
    Args:
        user: User to check
        required_role: Required role
        
    Returns:
        True if user has permission, False otherwise
    """
    if user.is_superuser:
        return True
    
    if required_role == UserRole.ADMIN:
        return user.role == UserRole.ADMIN
    
    # USER role is the default, everyone has it
    return True
