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

    # The post must belong to the authenticated user.
    assert data["user_id"] == registered_user["id"]

    # The database must generate the post ID.
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

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient,
    created_post: dict,
    registered_user: dict,
    logged_in_token: str,
):
    """Test liking a post and updating its total number of likes."""

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

    # The database must generate the like ID.
    assert isinstance(data["id"], int)

    # Retrieve the post to verify the aggregated like count.
    post_response = await async_client.get(f"/post/{created_post['id']}")

    post_data = post_response.json()

    assert post_response.status_code == status.HTTP_200_OK
    assert post_data["post"]["likes"] == 1


@pytest.mark.anyio
async def test_get_all_posts(
    async_client: AsyncClient,
    created_post: dict,
):
    """Test retrieving all posts with their like counts."""

    response = await async_client.get("/posts")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            **created_post,
            "likes": 0,
        }
    ]


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient,
    created_post: dict,
    created_comment: dict,
):
    """Test retrieving a post with its like count and comments."""

    response = await async_client.get(f"/post/{created_post['id']}")

    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data["post"] == {
        **created_post,
        "likes": 0,
    }
    assert data["comments"] == [created_comment]


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient,
    registered_user: dict,
    mocker,
):
    """Test that an expired access token is rejected."""

    # Force newly generated access tokens to expire immediately.
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
