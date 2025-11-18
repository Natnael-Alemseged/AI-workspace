from collections.abc import AsyncIterator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import ASYNC_DATABASE_URL, DATABASE_URL

# For SQLite, use StaticPool to avoid connection issues
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if ASYNC_DATABASE_URL.startswith("sqlite"):
    async_engine = create_async_engine(ASYNC_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    async_engine = create_async_engine(ASYNC_DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

# Export for background tasks
async_session_maker = AsyncSessionLocal

Base = declarative_base()


async def get_async_session() -> AsyncIterator[AsyncSession]:
    from app.core.logging import logger
    try:
        async with AsyncSessionLocal() as session:
            logger.debug("Async session created successfully")
            yield session
    except Exception as e:
        logger.error(f"Failed to create async session: {e}")
        raise
