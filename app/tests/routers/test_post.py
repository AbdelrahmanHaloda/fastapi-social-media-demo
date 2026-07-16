import pytest
from httpx import AsyncClient

""" Test post creation"""
@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient):
    body = "Test post"
    response = await async_client.post("/post", json={"body": "Test post"})
    assert response.status_code == 201
    assert {"id": 1, "body": body}.items() <= response.json().items()

""" Test get post with no body """
@pytest.mark.anyio
async def test_get_post_with_no_body(async_client: AsyncClient):
    response = await async_client.post("/post", json={})
    assert response.status_code == 422

""" Test get all posts """
@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/posts")
    assert response.status_code == 200
    assert response.json() == [created_post]

""" Test to get a post with its comments """
@pytest.mark.anyio
async def test_get_post_with_comments(async_client: AsyncClient, created_post: dict, created_comment: dict):
    post_id = created_post["id"]
    response = await async_client.get(f"/post/{post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["post"] == created_post
    assert data["comments"] == [created_comment]