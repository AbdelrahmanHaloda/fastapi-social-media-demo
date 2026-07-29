"""Pydantic models for validating user-related data."""

from pydantic import BaseModel


class User(BaseModel):
    """Represent the basic user information."""

    # Optional because the database assigns the ID when the user is created.
    id: int | None = None
    email: str


class UserIn(User):
    """Represent user data accepted during registration."""

    password: str
