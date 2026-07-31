"""Pydantic models for post likes."""

from pydantic import BaseModel


class PostLikeIn(BaseModel):
    """Data required to like a post."""

    post_id: int


class PostLike(PostLikeIn):
    """Like data returned by the API."""

    id: int
    user_id: int
