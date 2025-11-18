"""Topic management API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.users_complete import get_current_user
from app.core.logging import logger
from app.db import get_async_session
from app.models.user import User
from app.schemas.channel import (
    TopicCreate,
    TopicDetail,
    TopicListResponse,
    TopicMemberRead,
    TopicRead,
    TopicUpdate,
    UserForTopicAddition,
)
from app.services.socketio_service import emit_to_room
from app.services.topic import TopicService

router = APIRouter()


@router.post("/topics", response_model=TopicDetail, status_code=status.HTTP_201_CREATED)
async def create_topic(
    topic_data: TopicCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new topic (admin only)."""
    try:
        topic = await TopicService.create_topic(session, topic_data, current_user.id)
        
        # Notify members via Socket.IO
        await emit_to_room(
            str(topic.id),
            "topic_created",
            {
                "topic_id": str(topic.id),
                "channel_id": str(topic.channel_id),
                "name": topic.name,
                "created_by": str(current_user.id)
            }
        )
        
        return topic
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create topic"
        )


@router.get("/{channel_id}/topics", response_model=TopicListResponse)
async def get_channel_topics(
    channel_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get topics in a channel that the user is a member of."""
    try:
        topics, total = await TopicService.get_channel_topics(
            session, channel_id, page, page_size, current_user.id
        )
        
        has_more = (page * page_size) < total
        
        return TopicListResponse(
            topics=topics,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error getting channel topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get topics"
        )


@router.get("/topics/my", response_model=TopicListResponse)
async def get_my_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all topics the current user is a member of."""
    try:
        topics, total = await TopicService.get_user_topics(
            session, current_user.id, page, page_size
        )
        
        has_more = (page * page_size) < total
        
        return TopicListResponse(
            topics=topics,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error getting user topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get topics"
        )


@router.get("/topics/{topic_id}", response_model=TopicDetail)
async def get_topic(
    topic_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get a specific topic."""
    try:
        topic = await TopicService.get_topic_by_id(session, topic_id, current_user.id)
        
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found or you are not a member"
            )
        
        return topic
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get topic"
        )


@router.patch("/topics/{topic_id}", response_model=TopicRead)
async def update_topic(
    topic_id: UUID,
    topic_data: TopicUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update a topic (admin only)."""
    try:
        topic = await TopicService.update_topic(
            session, topic_id, current_user.id, topic_data
        )
        
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
        
        # Notify topic members
        await emit_to_room(
            str(topic_id),
            "topic_updated",
            {
                "topic_id": str(topic_id),
                "updated_by": str(current_user.id)
            }
        )
        
        return topic
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update topic"
        )


@router.get("/topics/{topic_id}/members", response_model=list[TopicMemberRead])
async def get_topic_members(
    topic_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all members of a topic (for @mentions)."""
    try:
        members = await TopicService.get_topic_members(
            session, topic_id, current_user.id
        )
        
        return members
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting topic members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get topic members"
        )


@router.get("/topics/{topic_id}/users-for-addition", response_model=list[UserForTopicAddition])
async def get_users_for_topic_addition(
    topic_id: UUID,
    search: Optional[str] = Query(None, description="Search by email or name"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all users with a flag indicating if they're already members (admin only)."""
    try:
        users = await TopicService.get_users_for_topic_addition(
            session, topic_id, current_user.id, search
        )
        
        return users
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting users for topic addition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users for topic addition"
        )


@router.post("/topics/{topic_id}/members/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_topic_member(
    topic_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Add a member to a topic (admin only)."""
    try:
        member = await TopicService.add_member(
            session, topic_id, current_user.id, user_id
        )
        
        # Notify topic members
        await emit_to_room(
            str(topic_id),
            "member_added",
            {
                "topic_id": str(topic_id),
                "user_id": str(user_id),
                "added_by": str(current_user.id)
            }
        )
        
        return {"message": "Member added successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add member"
        )


@router.delete("/topics/{topic_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_topic_member(
    topic_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove a member from a topic (admin only)."""
    try:
        success = await TopicService.remove_member(
            session, topic_id, current_user.id, user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Notify topic members
        await emit_to_room(
            str(topic_id),
            "member_removed",
            {
                "topic_id": str(topic_id),
                "user_id": str(user_id),
                "removed_by": str(current_user.id)
            }
        )
        
        return None
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member"
        )
