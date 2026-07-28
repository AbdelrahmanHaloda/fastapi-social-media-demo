import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler

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


@app.exception_handler(HTTPException)
async def http_exception_logging_handler(
    request: Request,
    exc: HTTPException,
):
    """Log HTTP exceptions before returning FastAPI's standard response."""

    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING

    logger.log(
        log_level,
        "HTTP exception: method=%s, path=%s, status=%s, detail=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )

    return await http_exception_handler(request, exc)
