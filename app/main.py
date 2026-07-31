"""FastAPI application setup, lifecycle management, and exception handling."""

import logging
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler

from app.database import database
from app.logging_conf import configure_logging
from app.routers.like import router as like_router
from app.routers.post import router as post_router
from app.routers.user import router as user_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown resources."""

    configure_logging()

    logger.info("Starting application")

    # Establish the shared asynchronous database connection during startup.
    await database.connect()
    logger.info("Database connection established")

    try:
        yield
    finally:
        # Release the database connection when the application shuts down.
        await database.disconnect()
        logger.info("Database connection closed")


app = FastAPI(lifespan=lifespan)

# Attach a correlation ID to each request for traceable application logs.
app.add_middleware(CorrelationIdMiddleware)

# Register the application's API routes.
app.include_router(post_router)
app.include_router(user_router)
app.include_router(like_router)


@app.exception_handler(HTTPException)
async def http_exception_logging_handler(
    request: Request,
    exc: HTTPException,
):
    """Log HTTP exceptions before returning FastAPI's standard response."""

    # Treat client errors as warnings and server errors as failures.
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
