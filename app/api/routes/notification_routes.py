"""API routes for FCM Push Notification subscriptions."""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models.user import PushSubscription, User

# Import current user dependency
try:
    from app.api.routes.users_complete import get_current_active_user as current_active_user
except ImportError:
    from app.api.routes.auth import current_active_user


router = APIRouter(prefix="/notifications", tags=["notifications"])


# Pydantic models
class PushSubscriptionCreate(BaseModel):
    """Schema for creating a push subscription (FCM token)."""
    endpoint: str  # FCM token


class PushSubscriptionResponse(BaseModel):
    """Schema for push subscription response."""
    id: str
    endpoint: str
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("/subscribe", response_model=PushSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_to_push(
    subscription: PushSubscriptionCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Subscribe to FCM push notifications.
    
    Creates a new FCM push subscription for the current user.
    If a subscription with the same endpoint (FCM token) already exists, it will be updated.
    """
    # Check if subscription already exists
    result = await session.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == current_user.id,
            PushSubscription.endpoint == subscription.endpoint
        )
    )
    existing_subscription = result.scalar_one_or_none()
    
    if existing_subscription:
        # Subscription already exists, just return it
        await session.commit()
        await session.refresh(existing_subscription)
        
        return PushSubscriptionResponse(
            id=str(existing_subscription.id),
            endpoint=existing_subscription.endpoint,
            created_at=existing_subscription.created_at.isoformat()
        )
    
    # Create new subscription
    new_subscription = PushSubscription(
        user_id=current_user.id,
        endpoint=subscription.endpoint
    )
    
    session.add(new_subscription)
    await session.commit()
    await session.refresh(new_subscription)
    
    return PushSubscriptionResponse(
        id=str(new_subscription.id),
        endpoint=new_subscription.endpoint,
        created_at=new_subscription.created_at.isoformat()
    )


@router.delete("/unsubscribe/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_from_push(
    subscription_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Unsubscribe from FCM push notifications.
    
    Deletes a push subscription by ID. Users can only delete their own subscriptions.
    """
    try:
        subscription_uuid = uuid.UUID(subscription_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription ID format"
        )
    
    # Get subscription
    result = await session.execute(
        select(PushSubscription).where(
            PushSubscription.id == subscription_uuid,
            PushSubscription.user_id == current_user.id
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    await session.delete(subscription)
    await session.commit()
    
    return None


@router.delete("/unsubscribe-by-endpoint", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe_by_endpoint(
    endpoint: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Unsubscribe from FCM push notifications by endpoint.
    
    Deletes a push subscription by FCM token (endpoint). Useful when subscription ID is not available.
    """
    # Get subscription
    result = await session.execute(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == current_user.id
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    await session.delete(subscription)
    await session.commit()
    
    return None


@router.get("/subscriptions", response_model=List[PushSubscriptionResponse])
async def get_user_subscriptions(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all FCM push subscriptions for the current user.
    
    Returns a list of all active FCM push subscriptions.
    """
    result = await session.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == current_user.id
        )
    )
    subscriptions = result.scalars().all()
    
    return [
        PushSubscriptionResponse(
            id=str(sub.id),
            endpoint=sub.endpoint,
            created_at=sub.created_at.isoformat()
        )
        for sub in subscriptions
    ]
