"""Shared fixtures and helper functions for post, comment, and like tests."""

import pytest
from httpx import AsyncClient

from app.tests.helpers import create_comment, like_post


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
