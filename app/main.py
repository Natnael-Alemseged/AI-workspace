# Main application entry point
import socketio

from app.api.routes.ai import router as ai_router
from app.api.routes.api import router as api_router
from app.api.routes.auth import router as auth_router
from app.api.routes.channels import router as channels_router
from app.api.routes.chat import router as chat_router
from app.core.config import ALLOWED_ORIGINS, API_PREFIX, DEBUG, PROJECT_NAME, VERSION, SECRET_KEY
from app.core.events import create_start_app_handler
from app.services.socketio_service import sio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.services.redis_client import redis_client


def get_application() -> FastAPI:
    application = FastAPI(title=PROJECT_NAME, debug=DEBUG, version=VERSION)


    # @application.on_event("startup")
    # async def startup_event():
    #     try:
    #         redis_client.client.ping()
    #         print("🚀 Redis connected successfully")
    #     except Exception as e:
    #         print("❌ Redis connection failed:", e)
    #
    # return application

    # Session middleware for OAuth (must be added before other middleware)
    application.add_middleware(
        SessionMiddleware,
        secret_key=str(SECRET_KEY),
        max_age=3600,  # 1 hour session timeout
        same_site="lax",
        https_only=False  # Set to True in production with HTTPS
    )

    # CORS middleware for OAuth support
    application.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=API_PREFIX)
    application.include_router(ai_router, prefix=API_PREFIX)
    application.include_router(auth_router, prefix=API_PREFIX)
    application.include_router(chat_router, prefix=API_PREFIX)
    application.include_router(channels_router, prefix=API_PREFIX)
    application.add_event_handler("startup", create_start_app_handler(application))
    return application


app = get_application()

# Mount Socket.IO app
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path="/socket.io"
)

# Export socket_app as the main ASGI application
app = socket_app
