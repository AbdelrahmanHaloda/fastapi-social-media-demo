"""Tests for post creation, retrieval, authentication, likes, and sorting."""

import pytest
from fastapi import status
from httpx import AsyncClient

from app import security
from app.tests.routers.conftest import create_post, like_post


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
    assert data["user_id"] == registered_user["id"]
    assert isinstance(data["id"], int)

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
@pytest.mark.parametrize(
    "sorting, expected_indices",
    [
        ("new", [1, 0]),
        ("old", [0, 1]),
    ],
)
async def test_get_all_posts_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_indices: list[int],
):
    """Test sorting posts from newest or oldest."""

    first_post = await create_post(
        "Test post 1",
        async_client,
        logged_in_token,
    )
    second_post = await create_post(
        "Test post 2",
        async_client,
        logged_in_token,
    )

    response = await async_client.get(
        "/posts",
        params={"sorting": sorting},
    )

    assert response.status_code == status.HTTP_200_OK

    post_ids = [post["id"] for post in response.json()]
    created_posts = [first_post, second_post]

    expected_order = [created_posts[index]["id"] for index in expected_indices]

    assert post_ids == expected_order


@pytest.mark.anyio
async def test_get_all_posts_sort_likes(
    async_client: AsyncClient,
    logged_in_token: str,
):
    """Test sorting posts by their number of likes."""

    first_post = await create_post(
        "Test post 1",
        async_client,
        logged_in_token,
    )
    second_post = await create_post(
        "Test post 2",
        async_client,
        logged_in_token,
    )

    await like_post(
        first_post["id"],
        async_client,
        logged_in_token,
    )

    response = await async_client.get(
        "/posts",
        params={"sorting": "most_likes"},
    )

    assert response.status_code == status.HTTP_200_OK

    post_ids = [post["id"] for post in response.json()]

    assert post_ids == [
        first_post["id"],
        second_post["id"],
    ]


@pytest.mark.anyio
async def test_get_all_posts_wrong_sorting(
    async_client: AsyncClient,
):
    """Test that an unsupported sorting value fails validation."""

    response = await async_client.get(
        "/posts",
        params={"sorting": "wrong"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


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
