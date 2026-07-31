"""Shared fixtures and helper functions for post, comment, and like tests."""

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

    # Raise an exception if the request was unsuccessful.
    response.raise_for_status()

    return response.json()


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
    """Provide a comment attached to the test post."""

    return await create_comment(
        body="Test comment",
        post_id=created_post["id"],
        async_client=async_client,
        logged_in_token=logged_in_token,
    )


async def like_post(
    post_id: int,
    async_client: AsyncClient,
    logged_in_token: str,
) -> dict:
    """Like a post as the authenticated user and return the response data."""

    response = await async_client.post(
        "/like",
        json={"post_id": post_id},
        headers={
            "Authorization": f"Bearer {logged_in_token}",
        },
    )

    response.raise_for_status()

    return response.json()


@pytest.fixture()
async def created_like(
    async_client: AsyncClient,
    created_post: dict,
    logged_in_token: str,
) -> dict:
    """Provide a like associated with the test post and authenticated user."""

    return await like_post(
        post_id=created_post["id"],
        async_client=async_client,
        logged_in_token=logged_in_token,
    )
