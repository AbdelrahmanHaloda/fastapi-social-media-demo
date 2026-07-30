import pytest
from fastapi import status
from httpx import AsyncClient, Response


async def register_user(
    async_client: AsyncClient,
    email: str,
    password: str,
) -> Response:
    """Send a user registration request."""

    return await async_client.post(
        "/register",
        json={
            "email": email,
            "password": password,
        },
    )


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    response = await register_user(
        async_client,
        "test@example.net",
        "1234",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert "User created" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_user_already_exists(
    async_client: AsyncClient,
    registered_user: dict,
):
    response = await register_user(
        async_client,
        registered_user["email"],
        registered_user["password"],
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_user_not_exists(async_client: AsyncClient):
    response = await async_client.post(
        "/token",
        json={
            "email": "missing@example.net",
            "password": "1234",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]

@pytest.mark.anyio
async def test_login_user(
    async_client: AsyncClient,
    registered_user: dict,
):
    response = await async_client.post(
        "/token",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["access_token"]
    assert response_data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_user_wrong_password(
    async_client: AsyncClient,
    registered_user: dict,
):
    response = await async_client.post(
        "/token",
        json={
            "email": registered_user["email"],
            "password": "wrong-password",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]
