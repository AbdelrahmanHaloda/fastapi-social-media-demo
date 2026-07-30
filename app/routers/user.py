"""API endpoints for user registration."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.database import database, user_table
from app.models.user import UserIn
from app.security import get_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=201)
async def register(user: UserIn):
    """Register a new user after confirming the email is not already in use."""

    # Prevent multiple accounts from being registered with the same email.
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=" A user with that email already exists !",
        )

    # TODO: Hash the password before storing it in the database.
    query = user_table.insert().values(
        email=user.email,
        password=user.password,
    )

    logger.debug(query)
    await database.execute(query)

    return {"detail": "User created"}
