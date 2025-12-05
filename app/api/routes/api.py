from fastapi import APIRouter

from app.api.routes import ai, conversations, gmail, search, notification_routes, direct_message_routes

router = APIRouter()

# Include Gmail routes
router.include_router(gmail.router)

# Include Search routes
router.include_router(search.router)

# Include AI routes
router.include_router(ai.router)

# Include Conversations routes
router.include_router(conversations.router)

# Include Notification routes
router.include_router(notification_routes.router)

# Include Direct Message routes
router.include_router(direct_message_routes.router)

# Include Agent routes
# router.include_router(agent.router)
