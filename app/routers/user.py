"""API endpoints for user registration and authentication."""

from fastapi import APIRouter, HTTPException, status

from app.database import database, user_table
from app.models.user import UserIn
from app.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user,
)

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserIn) -> dict[str, str]:
    """Register a new user if the email is not already in use."""

    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists.",
        )

    # Hash the password before storing it in the database.
    query = user_table.insert().values(
        email=user.email,
        password=get_password_hash(user.password),
    )
    await database.execute(query)

    return {"detail": "User created"}


@router.post("/token")
async def login(user: UserIn) -> dict[str, str]:
    """Authenticate a user and return a signed JWT access token."""

    # Returns the database user when the credentials are valid.
    authenticated_user = await authenticate_user(
        user.email,
        user.password,
    )

    # Store the email in the token's subject claim.
    access_token = create_access_token(authenticated_user.email)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
