# app/db.py

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from typing import AsyncIterator
import urllib.parse

from app.core.config import ASYNC_DATABASE_URL
from app.core.logging import logger


# Take the raw URL from config
db_url = ASYNC_DATABASE_URL.strip()

# Ensure correct driver (postgres:// → postgresql+asyncpg://)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

# Parse URL and safely remove sslmode from query string (prevents duplicate)
parsed = urllib.parse.urlparse(db_url)
query_params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
query_params.pop("sslmode", None)  # Remove sslmode if present




# Rebuild clean URL without sslmode parameter
clean_url = urllib.parse.urlunparse((
    parsed.scheme,
    parsed.netloc,
    parsed.path,
    parsed.params,
    urllib.parse.urlencode(query_params, doseq=True),
    parsed.fragment
)).rstrip("?")  # Remove trailing ? if no other params

# SSL handled correctly via connect_args (this is the only right way for asyncpg + Neon)
connect_args = {
    "ssl": "require",                    # Required for Neon
    "server_settings": {"jit": "off"},   # Faster cold starts
    "timeout": 10,
}

# Final bulletproof engine
async_engine = create_async_engine(
    clean_url,
    echo=False,
    future=True,
    pool_pre_ping=True,       # Critical: survives Heroku dyno sleep
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    connect_args=connect_args,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI routes
async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("Async DB session opened")
            yield session
        except Exception as exc:
            logger.opt(exception=True).error("Database session error: {}", exc)
            await session.rollback()
            raise
        finally:
            await session.close()