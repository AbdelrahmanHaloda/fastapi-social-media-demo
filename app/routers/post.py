"""API routes for creating and retrieving posts and comments."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import comment_table, database, post_table
from app.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)
from app.models.user import User
from app.security import get_current_user

logger = logging.getLogger(__name__)

# Groups the post and comment endpoints so they can be registered
# together in the main FastAPI application.
router = APIRouter()


async def find_post(post_id: int):
    """Return a post by ID, or None when it does not exist."""

    logger.debug("Looking up post: post_id=%s", post_id)

    query = post_table.select().where(post_table.c.id == post_id)


    # Return the matching database record, or None if no row exists.
    post = await database.fetch_one(query)

    logger.debug(
        "Post lookup completed: post_id=%s, found=%s",
        post_id,
        post is not None,
    )

    return post


@router.post(
    "/post",
    response_model=UserPost,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    post: UserPostIn,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a post for an authenticated user."""


    # Convert the validated request model into values accepted by SQLAlchemy.
    data = post.model_dump()

    query = post_table.insert().values(data)
    # For the current SQLite database, execute returns the generated
    # primary-key value of the inserted row.
    last_record_id = await database.execute(query)

    logger.info("Post created: post_id=%s", last_record_id)

    return {
        **data,
        "id": last_record_id,
    }


@router.get(
    "/posts",
    response_model=list[UserPost],
)
async def get_posts():
    """Return all posts."""
    logger.debug("Fetching all posts")

    query = post_table.select()
    posts = await database.fetch_all(query)

    logger.debug("Posts retrieved: count=%s", len(posts))

    return posts


@router.post(
    "/comment",
    response_model=Comment,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    comment: CommentIn,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a comment on an existing post for an authenticated user."""

    post = await find_post(comment.post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    data = comment.model_dump()

    query = comment_table.insert().values(data)
    last_record_id = await database.execute(query)

    logger.info(
        "Comment created: comment_id=%s, post_id=%s",
        last_record_id,
        comment.post_id,
    )

    return {
        **data,
        "id": last_record_id,
    }


@router.get(
    "/comment/{post_id}/comment",
    response_model=list[Comment],
)
async def get_comments_on_post(post_id: int):
    """Return all comments associated with a post."""
    logger.debug("Fetching comments: post_id=%s", post_id)

    query = comment_table.select().where(comment_table.c.post_id == post_id)

    comments = await database.fetch_all(query)

    logger.debug(
        "Comments retrieved: post_id=%s, count=%s",
        post_id,
        len(comments),
    )

    return comments


@router.get(
    "/post/{post_id}",
    response_model=UserPostWithComments,
)
async def get_post_with_comments(post_id: int):
    """Return a post together with its comments."""
    logger.debug(
        "Fetching post with comments: post_id=%s",
        post_id,
    )

    post = await find_post(post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    comments = await get_comments_on_post(post_id)

    return {
        "post": post,
        "comments": comments,
    }
