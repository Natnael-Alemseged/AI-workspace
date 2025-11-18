from fastapi import APIRouter

from app.api.routes import ai, conversations, gmail, search

router = APIRouter()

# Include Gmail routes
router.include_router(gmail.router)

# Include Search routes
router.include_router(search.router)

# Include AI routes
router.include_router(ai.router)

# Include Conversations routes
router.include_router(conversations.router)

# Include Agent routes
# router.include_router(agent.router)
