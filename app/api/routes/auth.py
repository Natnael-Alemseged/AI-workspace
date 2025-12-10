from fastapi import APIRouter

from app.api.routes import auth_custom, users_complete, admin_routes

router = APIRouter()

# Custom auth endpoints (replacing FastAPI-Users)
router.include_router(auth_custom.router, prefix="/auth", tags=["auth"])
router.include_router(users_complete.router, prefix="/users", tags=["users"])

# Admin endpoints
router.include_router(admin_routes.router, prefix="/admin", tags=["admin"])

# Google OAuth endpoints are now available at:
# - GET /auth/google/authorize - Initiate OAuth flow
# - GET /auth/google/callback - OAuth callback handler
# - GET /auth/google/status - Check OAuth connection status
