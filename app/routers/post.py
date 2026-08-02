"""API routes for creating and retrieving posts and comments."""

import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.database import (
    comment_table,
    database,
    like_table,
    post_table,
)
from app.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
    UserPostWithLikes,
)
from app.models.user import User
from app.security import get_current_user
from app.tasks import generate_and_add_to_post

logger = logging.getLogger(__name__)


# Groups the post and comment endpoints so they can be registered
# together in the main FastAPI application.
router = APIRouter()


# Reusable query that returns each post together with its like count.
#
# outerjoin() keeps posts that have no likes.
# count(like_table.c.id) produces 0 when a post has no likes.
# SQLAlchemy infers the join condition from the foreign key:
# likes.post_id -> posts.id
select_posts_likes = (
    sqlalchemy.select(
        post_table,
        sqlalchemy.func.count(like_table.c.id).label("likes"),
    )
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)


async def find_post(post_id: int):
    """Return a post by ID, or None if it does not exist."""

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
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    background_tasks: BackgroundTasks,
    request: Request,
    prompt: str | None = None,
):
    """Create a post for the authenticated user."""

    # The post body comes from the validated request.
    # The user ID comes from the authenticated user's token.data = {
    data = {
        **post.model_dump(),
        "user_id": current_user.id,
    }

    query = post_table.insert().values(data)

    last_record_id = await database.execute(query)

    if prompt:
        post_url = str(
            request.url_for(
                "get_post_with_comments",
                post_id=last_record_id,
            )
        )

        background_tasks.add_task(
            generate_and_add_to_post,
            current_user.email,
            last_record_id,
            post_url,
            database,
            prompt,
        )

    logger.info(
        "Post created: post_id=%s, user_id=%s",
        last_record_id,
        current_user.id,
    )

    return {
        **data,
        "id": last_record_id,
    }

class PostSorting(str, Enum):
    NEW = "new"
    OLD = "old"
    MOST_LIKES = "most_likes"

@router.get(
    "/posts",
    response_model=list[UserPostWithLikes],
)
async def get_posts(sorting: PostSorting = PostSorting.NEW ):
    """Return all posts together with their like counts."""

    logger.debug("Fetching all posts with like counts")

    if sorting == PostSorting.NEW:
        query = select_posts_likes.order_by(post_table.c.id.desc())
    elif sorting == PostSorting.OLD:
        query = select_posts_likes.order_by(post_table.c.id.asc())
    elif sorting == PostSorting.MOST_LIKES:
        query = select_posts_likes.order_by(sqlalchemy.desc("likes"))
    
    posts = await database.fetch_all(query)

    logger.debug(
        "Posts retrieved: count=%s",
        len(posts),
    )

    return posts


@router.post(
    "/comment",
    response_model=Comment,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    comment: CommentIn,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    """Create a comment on an existing post."""

    # Confirm that the target post exists before inserting the comment.
    post = await find_post(comment.post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    # The comment data comes from the request.
    # The user ID comes from the authenticated user's token.
    data = {
        **comment.model_dump(),
        "user_id": current_user.id,
    }

    query = comment_table.insert().values(data)
    last_record_id = await database.execute(query)

    logger.info(
        "Comment created: comment_id=%s, post_id=%s, user_id=%s",
        last_record_id,
        comment.post_id,
        current_user.id,
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

    logger.debug(
        "Fetching comments: post_id=%s",
        post_id,
    )

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
    """Return one post with its like count and comments."""

    logger.debug(
        "Fetching post with comments and likes: post_id=%s",
        post_id,
    )

    # Reuse the base query and restrict it to the requested post.
    query = select_posts_likes.where(post_table.c.id == post_id)

    logger.debug(query)

    post = await database.fetch_one(query)

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
