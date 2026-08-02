"""Shared pytest fixtures for API and authentication tests."""

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient, Request, Response

from app.tests.helpers import create_post

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
        yield database
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

@pytest.fixture(autouse = True)
def mock_httpx_client(mocker):
    """Mock the httpx.AsyncClient to prevent real HTTP requests during tests."""
    mocked_client = mocker.patch("app.tasks.httpx.AsyncClient")
    mocked_async_client = Mock()
    response = Response(status_code = status.HTTP_200_OK, content = "", request = Request("POST", "//"))
    mocked_async_client.post = AsyncMock(return_value = response)
    mocked_client.return_value.__aenter__.return_value = mocked_async_client

    return mocked_async_client

@pytest.fixture()
async def created_post(
    async_client: AsyncClient,
    logged_in_token: str,
) -> dict:
    """Provide a newly created post to tests that require one."""

    return await create_post(
        body="Test post",
        async_client=async_client,
        logged_in_token=logged_in_token,
    )
