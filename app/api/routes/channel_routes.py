"""Channel CRUD API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.users_complete import get_current_user
from app.core.logging import logger
from app.db import get_async_session
from app.models.user import User
from app.schemas.channel import (
    ChannelCreate,
    ChannelListResponse,
    ChannelRead,
    ChannelUpdate,
)
from app.services.channel import ChannelService

router = APIRouter()


@router.post("/", response_model=ChannelRead, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_data: ChannelCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new channel (admin only)."""
    try:
        channel = await ChannelService.create_channel(session, channel_data, current_user.id)
        return channel
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create channel"
        )


@router.get("/", response_model=ChannelListResponse)
async def get_all_channels(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get channels where the user is a member of at least one topic."""
    try:
        channels = await ChannelService.get_all_channels(session, current_user.id)
        return ChannelListResponse(channels=channels, total=len(channels))
        
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get channels"
        )


@router.get("/{channel_id}", response_model=ChannelRead)
async def get_channel(
    channel_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific channel."""
    try:
        channel = await ChannelService.get_channel_by_id(session, channel_id)
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )
        
        return channel
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting channel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get channel"
        )


@router.patch("/{channel_id}", response_model=ChannelRead)
async def update_channel(
    channel_id: UUID,
    channel_data: ChannelUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update a channel (admin only)."""
    try:
        channel = await ChannelService.update_channel(
            session, channel_id, current_user.id, channel_data
        )
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )
        
        return channel
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating channel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update channel"
        )


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a channel (admin only)."""
    try:
        success = await ChannelService.delete_channel(
            session, channel_id, current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Channel not found"
            )
        
        return None
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting channel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete channel"
        )
