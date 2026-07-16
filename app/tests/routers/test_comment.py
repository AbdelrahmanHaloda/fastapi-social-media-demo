import pytest
from httpx import AsyncClient

# async def create_comment(body: str, post_id: int, async_client: AsyncClient) -> dict:
#     response = await async_client.post(f"/post/{post_id}/comment", json={"body": body})
#     return response.json()  

""" Test comment creation """
@pytest.mark.anyio
async def test_create_comment(async_client: AsyncClient, created_post: dict):
    
    json = {"body": "test comment", "post_id": created_post["id"]}
    response = await async_client.post("/comment", json=json)
    
    data =response.json()
    
    assert response.status_code == 201
    assert data["body"] == response.json()["body"]
    assert data["post_id"] == response.json()["post_id"]
    assert response.json()["id"] == 1
    # assert response.json() == {
    # "id": 1,
    # "body": response.json()["body"],
    # "post_id": response.json()["post_id"]
    # }
    #-------------------------------------------
    # assert {
    #     "id": 1,
    #     "body": "test comment",
    #     "post_id": created_post["id"]
    # }.items() <= response.json().items()

"""Test create comment with non-existent post"""
@pytest.mark.anyio
async def test_create_comment_with_nonexistent_post(async_client: AsyncClient):
    body = "Test comment"
    post_id = 1  # Non-existent post ID
    response = await async_client.post("/comment", json={"body": body, "post_id": post_id})
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


"""Test get comments for a specific post"""
@pytest.mark.anyio
async def test_get_comments_on_post(async_client: AsyncClient, created_post: dict, created_comment: dict):
    post_id = created_post["id"]
    response = await async_client.get(f"/comment/{post_id}/comment")
    assert response.status_code == 200
    assert response.json() == [created_comment]


"""Test get comments for a post with no comments"""
@pytest.mark.anyio
async def test_get_comments_on_empty_post(
    async_client: AsyncClient, created_post: dict):
    post_id = created_post["id"]
    response = await async_client.get(f"/comment/{post_id}/comment")
    assert response.status_code == 200
    assert response.json() == []