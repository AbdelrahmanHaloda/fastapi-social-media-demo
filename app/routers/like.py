"""API endpoints for post likes."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import database, like_table
from app.models.like import PostLike, PostLikeIn
from app.models.user import User
from app.routers.post import find_post
from app.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/like",
    response_model=PostLike,
    status_code=status.HTTP_201_CREATED,
)
async def like_post(
    like: PostLikeIn,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Like an existing post as the authenticated user."""

    logger.info(
        "Liking post: post_id=%s, user_id=%s",
        like.post_id,
        current_user.id,
    )

    post = await find_post(like.post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    data = {
        **like.model_dump(),
        "user_id": current_user.id,
    }

    query = like_table.insert().values(data)

    logger.debug("Like insertion query: %s", query)

    last_record_id = await database.execute(query)

    return {
        **data,
        "id": last_record_id,
    }
