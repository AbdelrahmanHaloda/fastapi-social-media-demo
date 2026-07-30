import pytest

from app import security


@pytest.mark.anyio
async def test_password_hashes():
    password = "test1234"
    hashed_password = security.get_password_hash(password)

    assert hashed_password != password
    assert security.verify_password(password, hashed_password)
    assert not security.verify_password("wrong-password", hashed_password)

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
