"""Security utilities and database operations used by authentication workflows."""

import logging

from passlib.context import CryptContext

from app.database import database, user_table

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_user(email: str):
    """Retrieve a user record by email, or return None if not found."""

    logger.debug("Fetching user from the database", extra={"email": email})

    query = user_table.select().where(user_table.c.email == email)
    return await database.fetch_one(query)
