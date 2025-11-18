# app/core/events.py

from typing import Callable

from fastapi import FastAPI
from loguru import logger
from sqlalchemy.exc import OperationalError

from app.db import Base, async_engine  # ← this is correct now


def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/verified successfully")
        except OperationalError as e:
            logger.error(f"Failed to connect to database on startup: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error during DB init: {e}")

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        logger.info("Application shutdown complete")

    return stop_app