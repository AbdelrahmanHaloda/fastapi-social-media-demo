import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import database
from app.logging_conf import configure_logging
from app.routers.post import router as post_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    logger.info("Starting application")

    await database.connect()
    logger.info("Database connection established")

    try:
        yield
    finally:
        await database.disconnect()
        logger.info("Database connection closed")

app = FastAPI(lifespan=lifespan)


app.include_router(post_router)

