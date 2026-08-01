import httpx
import pytest
from fastapi import status

from app.tasks import APIResponseError, send_simple_email


@pytest.mark.anyio
async def test_send_simple_email(mock_httpx_client):
    """Test sending a simple email using the send_simple_email function."""

    # Call the function to send an email
    await send_simple_email(
        to="example@test.net",
        subject="Test Subject",
        body="Test body"
    )
    mock_httpx_client.post.assert_called()


@pytest.mark.anyio
async def test_send_email_api_error(mock_httpx_client):
    """Test that send_simple_email raises APIResponseError on HTTP error."""

    # Configure the mock to raise an HTTPStatusError
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content="",
        request=httpx.Request("POST", "//")
    )
    with pytest.raises(APIResponseError):
        await send_simple_email(
            to="text_example.com",
            subject="Test Subject",
            body="Test body"
        )
