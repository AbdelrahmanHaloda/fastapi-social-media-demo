"""Shared pytest fixtures for API and authentication tests."""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# Select the test configuration before importing application modules.
os.environ["ENV_STATE"] = "test"

from app.database import database, user_table
from app.main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Run asynchronous tests using asyncio."""

    return "asyncio"


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator[None, None]:
    """Connect to the test database for each test and disconnect afterward."""

    await database.connect()

    try:
        yield
    finally:
        await database.disconnect()


@pytest.fixture()
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an asynchronous HTTP client for testing the FastAPI app."""

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture()
async def registered_user(
    async_client: AsyncClient,
) -> dict[str, str | int]:
    """Register a test user and return its credentials and database ID."""

    user_details = {
        "email": "test@example.com",
        "password": "1234",
    }

    response = await async_client.post(
        "/register",
        json=user_details,
    )
    response.raise_for_status()

    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)

    assert user is not None

    return {
        **user_details,
        "id": user.id,
    }

@pytest.fixture()
async def confirmed_user(registered_user: dict) -> dict:

    query = (
        user_table.update()
        .where(user_table.c.email == registered_user["email"])
        .values(confirmed=True)
    )
    await database.execute(query)
    return registered_user

@pytest.fixture()
async def logged_in_token(
    async_client: AsyncClient,
    confirmed_user: dict[str, str | int],
) -> str:
    """Log in the confirmed test user and return its access token."""

    response = await async_client.post(
        "/token",
        json={
            "email": confirmed_user["email"],
            "password": confirmed_user["password"],
        },
    )
    response.raise_for_status()

    return response.json()["access_token"]
