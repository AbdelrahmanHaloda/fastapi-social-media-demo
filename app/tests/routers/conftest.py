"""Fixtures and helpers for post and comment router tests."""

import pytest
from httpx import AsyncClient


async def create_post(
    body: str,
    async_client: AsyncClient,
    logged_in_token: str,
) -> dict:
    """Create an authenticated post and return its response data."""

    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={
            "Authorization": f"Bearer {logged_in_token}",
        },
    )
    response.raise_for_status()

    return response.json()


@pytest.fixture()
async def created_post(
    async_client: AsyncClient,
    logged_in_token: str,
) -> dict:
    """Create a post for tests that require one."""

    return await create_post(
        "Test post",
        async_client,
        logged_in_token,
    )


async def create_comment(
    body: str,
    post_id: int,
    async_client: AsyncClient,
    logged_in_token: str,
) -> dict:
    """Create an authenticated comment and return its response data."""

    response = await async_client.post(
        "/comment",
        json={
            "body": body,
            "post_id": post_id,
        },
        headers={
            "Authorization": f"Bearer {logged_in_token}",
        },
    )
    response.raise_for_status()

    return response.json()


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient,
    created_post: dict,
    logged_in_token: str,
) -> dict:
    """Create a comment attached to the test post."""

    return await create_comment(
        "Test comment",
        created_post["id"],
        async_client,
        logged_in_token,
    )
