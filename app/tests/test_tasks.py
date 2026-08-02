import httpx
import pytest
from databases import Database
from fastapi import status

from app.database import post_table
from app.tasks import (
    APIResponseError,
    _generate_cute_creature_api,
    generate_and_add_to_post,
    send_simple_email,
)


@pytest.mark.anyio
async def test_send_simple_email(mock_httpx_client):
    """Test sending a simple email."""

    await send_simple_email(
        to="example@test.net",
        subject="Test Subject",
        body="Test body",
    )

    mock_httpx_client.post.assert_called()


@pytest.mark.anyio
async def test_send_email_api_error(mock_httpx_client):
    """Test that an HTTP error raises APIResponseError."""

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content="",
        request=httpx.Request("POST", "//"),
    )

    with pytest.raises(APIResponseError):
        await send_simple_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test body",
        )


@pytest.mark.anyio
async def test_generate_cute_creature_api_success(
    mock_httpx_client,
):
    """Test successful image generation."""

    json_data = {
        "output_url": "https://example.com/image.jpg",
    }

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=status.HTTP_200_OK,
        json=json_data,
        request=httpx.Request("POST", "//"),
    )

    result = await _generate_cute_creature_api("A cat")

    assert result == json_data


@pytest.mark.anyio
async def test_generate_cute_creature_api_error(
    mock_httpx_client,
):
    """Test that an image API HTTP error is handled."""

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content="",
        request=httpx.Request("POST", "//"),
    )

    with pytest.raises(
        APIResponseError,
        match="API request failed with status code 500",
    ):
        await _generate_cute_creature_api("A cat")


@pytest.mark.anyio
async def test_generate_cute_creature_api_json_error(
    mock_httpx_client,
):
    """Test that an invalid JSON response is handled."""

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=status.HTTP_200_OK,
        content="Not JSON",
        request=httpx.Request("POST", "//"),
    )

    with pytest.raises(
        APIResponseError,
        match="API response parsing failed",
    ):
        await _generate_cute_creature_api("A cat")


@pytest.mark.anyio
async def test_generate_and_add_to_post_success(
    mock_generate_cute_creature_api,
    created_post: dict,
    confirmed_user: dict,
    db: Database,
):
    """Test generating an image and adding its URL to a post."""

    json_data = {
        "output_url": "https://example.net/image.jpg",
    }

    mock_generate_cute_creature_api.return_value = json_data

    await generate_and_add_to_post(
        confirmed_user["email"],
        created_post["id"],
        "/post/1",
        db,
        "A cat",
    )

    query = post_table.select().where(post_table.c.id == created_post["id"])

    updated_post = await db.fetch_one(query)

    assert updated_post is not None
    assert updated_post["image_url"] == json_data["output_url"]
