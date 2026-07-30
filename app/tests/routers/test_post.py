"""Tests for post creation and retrieval endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient

from app import security


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient,
    logged_in_token: str,
):
    """Test creating a post with a valid access token."""

    payload = {"body": "Test post"}

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
async def test_get_all_posts(
    async_client: AsyncClient,
    created_post: dict,
):
    """Test retrieving all posts."""

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

    mocker.patch(
        "app.security.access_token_expire_minutes",
        return_value=-1,
    )

    token = security.create_access_token(registered_user["email"])

    response = await async_client.post(
        "/post",
        json={"body": "Test body"},
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Token has expired"
