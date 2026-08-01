import pytest
from fastapi import status
from jose import jwt

from app import security


@pytest.mark.anyio
async def test_access_token_expire_minutes():
    assert security.access_token_expire_minutes() == 30

@pytest.mark.anyio
async def test_confirm_token_expire_minutes():
    assert security.confirm_token_expire_minutes() == 1440

@pytest.mark.anyio
async def test_create_access_token():
    token = security.create_access_token("123")
    payload = jwt.decode(
        token,
        key=security.SECRET_TOKEN_KEY,
        algorithms=[security.ALGORITHM],
    )

    assert payload["sub"] == "123"
    assert payload["type"] == "access"
    assert "exp" in payload

@pytest.mark.anyio
async def test_create_confirmation_token():
    token = security.create_confirmation_token("123")
    payload = jwt.decode(
        token,
        key=security.SECRET_TOKEN_KEY,
        algorithms=[security.ALGORITHM],
    )

    assert payload["sub"] == "123"
    assert payload["type"] == "confirmation"
    assert "exp" in payload

@pytest.mark.anyio
async def test_get_subject_for_token_type_valid_confirmation():
    email = "test@example.com"
    token = security.create_confirmation_token(email)
    subject = security.get_subject_from_token_type(token, "confirmation")
    assert subject == email

@pytest.mark.anyio
async def test_get_subject_for_token_type_valid_access():
    email = "test@example.com"
    token = security.create_access_token(email)
    subject = security.get_subject_from_token_type(token, "access")
    assert subject == email

@pytest.mark.anyio
async def test_get_subject_for_token_type_valid_expired(mocker):
    mocker.patch("app.security.access_token_expire_minutes", return_value=-1)
    email = "test@example.com"
    token = security.create_access_token(email)
    with pytest.raises(security.HTTPException) as exception:
        security.get_subject_from_token_type(token, "access")
    assert exception.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exception.value.detail == "Token has expired"

@pytest.mark.anyio
async def test_get_subject_for_token_type_invalid_token():
    token = "Invalid token"
    with pytest.raises(security.HTTPException) as exception:
        security.get_subject_from_token_type(token, "access")
    assert exception.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exception.value.detail == "Invalid token"

@pytest.mark.anyio
async def test_get_subject_for_token_type_missing_sub():
    email = "test_example.com"
    token = security.create_access_token(email)
    payload = jwt.decode(
        token,
        key=security.SECRET_TOKEN_KEY,
        algorithms=[security.ALGORITHM],
    )
    del payload["sub"]
    token_without_sub = jwt.encode(
        payload,
        key=security.SECRET_TOKEN_KEY,
        algorithm=security.ALGORITHM,
    )
    with pytest.raises(security.HTTPException) as exception:
        security.get_subject_from_token_type(token_without_sub, "access")
    assert exception.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exception.value.detail == "Token is missing 'sub' field"

@pytest.mark.anyio
async def test_get_subject_for_token_type_wrong_type():
    email = "test_example.com"
    token = security.create_confirmation_token(email)
    with pytest.raises(security.HTTPException) as exception:
        security.get_subject_from_token_type(token, "access")
    assert exception.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exception.value.detail == "Token has incorrect type, expected 'access'" == exception.value.detail

@pytest.mark.anyio
async def test_password_hashes():
    password = "test1234"
    hashed_password = security.get_password_hash(password)

    assert hashed_password != password
    assert security.verify_password(password, hashed_password)
    assert not security.verify_password(
        "wrong-password",
        hashed_password,
    )


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])

    assert user is not None
    assert user.email == registered_user["email"]
    assert user.password != registered_user["password"]
    assert security.verify_password(
        registered_user["password"],
        user.password,
    )


@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("missing@example.com")
    assert user is None


@pytest.mark.anyio
async def test_authenticate_user(confirmed_user: dict):
    user = await security.authenticate_user(
        confirmed_user["email"],
        confirmed_user["password"],
    )
    assert user.email == confirmed_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    with pytest.raises(security.HTTPException) as exception:
        await security.authenticate_user(
            "missing@test.com",
            "1234",
        )
    assert exception.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exception.value.detail == "Invalid email or password"


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(
    registered_user: dict,
):
    with pytest.raises(security.HTTPException) as exception:
        await security.authenticate_user(
            registered_user["email"],
            "wrong-password",
        )
    assert exception.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exception.value.detail == "Invalid email or password"

@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)
    assert user.email == registered_user["email"]

@pytest.mark.anyio
async def test_get_current_invalid_user():
    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalid token")

@pytest.mark.anyio
async def test_get_current_wrong_type_token(registered_user: dict):
    token = security.create_confirmation_token(registered_user["email"])
    
    with pytest.raises(security.HTTPException):
        await security.get_current_user(token)