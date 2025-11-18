"""Channel and Topic API endpoints - Main router combining all sub-routers."""
from fastapi import APIRouter

from app.api.routes import (
    channel_routes,
    reaction_routes,
    topic_message_routes,
    topic_routes,
)

# Main router with /channels prefix
router = APIRouter(prefix="/channels", tags=["channels"])

# Include all sub-routers
# Channel CRUD endpoints (e.g., /channels, /channels/{channel_id})
router.include_router(channel_routes.router)

# Topic management endpoints (e.g., /channels/topics, /channels/{channel_id}/topics)
router.include_router(topic_routes.router)

# Topic message endpoints (e.g., /channels/topics/messages, /channels/topics/{topic_id}/messages)
router.include_router(topic_message_routes.router)

# Reaction endpoints (e.g., /channels/topics/messages/{message_id}/reactions)
router.include_router(reaction_routes.router)
