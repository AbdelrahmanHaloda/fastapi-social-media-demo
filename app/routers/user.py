"""API endpoints for user registration."""

from fastapi import APIRouter, HTTPException, status

from app.database import database, user_table
from app.models.user import UserIn
from app.security import get_password_hash, get_user

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserIn) -> dict[str, str]:
    """Register a new user if the email is not already in use."""

    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists.",
        )

    query = user_table.insert().values(
        email=user.email,
        password=get_password_hash(user.password),
    )
    await database.execute(query)

    return {"detail": "User created"}
