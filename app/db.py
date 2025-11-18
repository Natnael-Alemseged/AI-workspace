# app/db.py

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from typing import AsyncIterator
import os

from app.core.config import ASYNC_DATABASE_URL
from app.core.logging import logger

# === FINAL PRODUCTION-READY NEON + HEROKU CONFIG ===
# Fix URL + add critical connection options
db_url = ASYNC_DATABASE_URL

# Ensure correct driver
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

# Add sslmode=require for Neon (mandatory)
if "neon.tech" in db_url:
    separator = "&" if "?" in db_url else "?"
    db_url += f"{separator}sslmode=require"

# Create engine with production-safe settings
async_engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    pool_pre_ping=True,                    # Critical: detects dead connections
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    connect_args={
        "server_settings": {"jit": "off"},  # Speeds up first query after idle
        "timeout": 10,
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("Async DB session opened")
            yield session
        except Exception as exc:
            logger.error(f"Database session error: {exc}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()