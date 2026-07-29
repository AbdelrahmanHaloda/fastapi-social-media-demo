"""Security-related database operations used by authentication workflows."""

import logging

from app.database import database, user_table

logger = logging.getLogger(__name__)


async def get_user(email: str):
    """Retrieve a user record by email.

    Returns the matching database record when found; otherwise, the function
    implicitly returns None.
    """
    logger.debug("Fetching user from the database", extra={"email": email})

    query = user_table.select().where(user_table.c.email == email)
    result = await database.fetch_one(query)

    if result:
        return result
