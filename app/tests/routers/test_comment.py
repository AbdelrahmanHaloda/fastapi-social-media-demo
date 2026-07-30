"""Tests for comment creation and retrieval endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    registered_user: dict,
    logged_in_token: str,
):
    """Test creating an authenticated comment."""

    payload = {
        "body": "Test comment",
        "post_id": created_post["id"],
    }

    response = await async_client.post(
        "/comment",
        json=payload,
        headers={
            "Authorization": f"Bearer {logged_in_token}",
        },
    )

    data = response.json()

    assert response.status_code == 201
    assert data["body"] == payload["body"]
    assert data["post_id"] == payload["post_id"]
    assert data["user_id"] == registered_user["id"]
    assert isinstance(data["id"], int)


@pytest.mark.anyio
async def test_create_comment_with_nonexistent_post(
    async_client: AsyncClient,
    logged_in_token: str,
):
    """Test creating a comment for a post that does not exist."""

    response = await async_client.post(
        "/comment",
        json={
            "body": "Test comment",
            "post_id": 999_999,
        },
        headers={
            "Authorization": f"Bearer {logged_in_token}",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient,
    created_post: dict,
    created_comment: dict,
):
    """Test retrieving comments associated with a post."""

    response = await async_client.get(f"/comment/{created_post['id']}/comment")

    assert response.status_code == 200
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_comments_on_empty_post(
    async_client: AsyncClient,
    created_post: dict,
):
    """Test retrieving comments from a post with no comments."""

    response = await async_client.get(f"/comment/{created_post['id']}/comment")

    assert response.status_code == 200
    assert response.json() == []
