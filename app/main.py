from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import database
from app.routers.post import router as post_router


@asynccontextmanager 
async def lifespan(app: FastAPI):
    await database.connect()
    try:
        yield
    finally:
        await database.disconnect()

app = FastAPI(lifespan=lifespan)


app.include_router(post_router)

