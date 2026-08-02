from httpx import AsyncClient


async def create_post(
    body: str,
    async_client: AsyncClient,
    logged_in_token: str,
) -> dict:
    """Create an authenticated post and return its response data."""

    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={
            "Authorization": f"Bearer {logged_in_token}",
        },
    )

    # Raise an exception if the request was unsuccessful.
    response.raise_for_status()
    return response.json()

async def create_comment(
    body: str,
    post_id: int,
    async_client: AsyncClient,
    logged_in_token: str,
) -> dict:
    """Create an authenticated comment and return its response data."""

    response = await async_client.post(
        "/comment",
        json={
            "body": body,
            "post_id": post_id,
        },
        headers={
            "Authorization": f"Bearer {logged_in_token}",
        },
    )
    response.raise_for_status()
    return response.json()


async def like_post(
    post_id: int,
    async_client: AsyncClient,
    logged_in_token: str,
) -> dict:
    """Like a post as the authenticated user and return the response data."""

    response = await async_client.post(
        "/like",
        json={"post_id": post_id},
        headers={
            "Authorization": f"Bearer {logged_in_token}",
        },
    )
    response.raise_for_status()
    return response.json()
