"""Pydantic models for posts and their associated comments."""

from pydantic import BaseModel, ConfigDict


class UserPostIn(BaseModel):
    """Data required to create a post."""

    body: str


class UserPost(UserPostIn):
    """Post data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


class CommentIn(BaseModel):
    """Data required to create a comment."""

    body: str
    post_id: int


class Comment(CommentIn):
    """Comment data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


class UserPostWithComments(BaseModel):
    """A post together with all of its comments."""

    post: UserPost
    comments: list[Comment]
