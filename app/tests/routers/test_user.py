import pytest
from fastapi import Request, status
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
async def test_confirm_user(async_client: AsyncClient, mocker):
    """Test confirming a user with a valid confirmation token."""

    spy = mocker.spy(Request, "url_for")
    await register_user(
        async_client,
        "test@example.net",
        "1234"
    )   
    confirmation_url = str(spy.spy_return)
    response = await async_client.get(confirmation_url)
    assert response.status_code == status.HTTP_200_OK
    assert "User confirmed" in response.json()["detail"]

@pytest.mark.anyio
async def test_confirm_user_invalid_token(async_client: AsyncClient):
    """Test confirming a user with an invalid confirmation token."""

    response = await async_client.get("/confirm/invalid-token")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.anyio
async def test_confirm_user_expired_token(async_client: AsyncClient, mocker):
    """Test confirming a user with an expired confirmation token."""

    mocker.patch("app.security.confirm_token_expire_minutes", return_value=-1)
    spy = mocker.spy(Request, "url_for")
    await register_user(
        async_client,
        "test@example.com",
        "1234"
        )
    confirmation_url = str(spy.spy_return)
    response = await async_client.get(confirmation_url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token has expired" in response.json()["detail"]




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
    assert "Invalid email or password" in response.json()["detail"]

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
    assert "Invalid email or password" in response.json()["detail"]
