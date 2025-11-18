from typing import Callable

from fastapi import FastAPI
from loguru import logger
from sqlalchemy.exc import OperationalError

from app.db import Base, engine


def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        from app.db import async_engine
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except OperationalError:
            logger.exception("Failed to initialize database")

    return start_app
