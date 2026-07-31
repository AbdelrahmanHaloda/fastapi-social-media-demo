"""Tests for post creation, retrieval, authentication, and likes."""

import pytest
from fastapi import status
from httpx import AsyncClient

from app import security


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient,
    registered_user: dict,
    logged_in_token: str,
):
    """Test creating a post as an authenticated user."""

    payload = {
        "body": "Test post",
    }

    response = await async_client.post(
        "/post",
        json=payload,
        headers={
            "Authorization": f"Bearer {logged_in_token}",
        },
    )

    data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert data["body"] == payload["body"]

    # The post owner must come from the authenticated user's token.
    assert data["user_id"] == registered_user["id"]

    # The database should generate an integer ID.
    assert isinstance(data["id"], int)


@pytest.mark.anyio
async def test_create_post_with_no_body(
    async_client: AsyncClient,
    logged_in_token: str,
):
    """Test that creating a post without a body fails validation."""

    response = await async_client.post(
        "/post",
        json={},
        headers={
            "Authorization": f"Bearer {logged_in_token}",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient,
    created_post: dict,
    registered_user: dict,
    logged_in_token: str,
):
    """Test liking a post as an authenticated user."""

    response = await async_client.post(
        "/like",
        json={
            "post_id": created_post["id"],
        },
        headers={
            "Authorization": f"Bearer {logged_in_token}",
        },
    )

    data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert data["post_id"] == created_post["id"]

    # The like must belong to the authenticated user.
    assert data["user_id"] == registered_user["id"]
    assert isinstance(data["id"], int)


@pytest.mark.anyio
async def test_get_all_posts(
    async_client: AsyncClient,
    created_post: dict,
):
    """Test retrieving all existing posts."""

    response = await async_client.get("/posts")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [created_post]


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient,
    created_post: dict,
    created_comment: dict,
):
    """Test retrieving a post together with its comments."""

    response = await async_client.get(f"/post/{created_post['id']}")

    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["post"] == created_post
    assert data["comments"] == [created_comment]


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient,
    registered_user: dict,
    mocker,
):
    """Test that an expired access token is rejected."""

    # Force newly created tokens to be expired immediately.
    mocker.patch(
        "app.security.access_token_expire_minutes",
        return_value=-1,
    )

    expired_token = security.create_access_token(registered_user["email"])

    response = await async_client.post(
        "/post",
        json={
            "body": "Test body",
        },
        headers={
            "Authorization": f"Bearer {expired_token}",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": "Token has expired",
    }
