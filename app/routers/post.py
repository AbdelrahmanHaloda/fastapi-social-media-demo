"""API routes for creating and retrieving posts and comments."""

from fastapi import APIRouter, HTTPException

from app.database import comment_table, database, post_table
from app.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)

# Groups the post and comment endpoints so they can be registered
# together in the main FastAPI application.
router = APIRouter()


async def find_post(post_id: int):
    """Retrieve a single post by its database ID."""

    # Build a SELECT query restricted to the requested post ID.
    query = post_table.select().where(post_table.c.id == post_id)

    # Return the matching database record, or None if no row exists.
    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(post: UserPostIn):
    """Create and return a new post."""

    # Convert the validated request model into values accepted by SQLAlchemy.
    data = post.model_dump()

    # Build and execute the INSERT statement.
    query = post_table.insert().values(data)

    # For the current SQLite database, execute returns the generated
    # primary-key value of the inserted row.
    last_record_id = await database.execute(query)

    # Combine the submitted fields with the database-generated ID.
    return {**data, "id": last_record_id}


@router.get("/posts", response_model=list[UserPost])
async def get_posts():
    """Return all posts stored in the database."""

    # Build a SELECT query covering every row in the posts table.
    query = post_table.select()

    # fetch_all returns a list of database records.
    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(comment: CommentIn):
    """Create a comment for an existing post."""

    # Verify that the referenced post exists before inserting the comment.
    post = await find_post(comment.post_id)

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found",
        )

    # Convert the validated request model into database column values.
    data = comment.model_dump()

    # Build and execute the comment INSERT statement.
    query = comment_table.insert().values(data)
    last_record_id = await database.execute(query)

    # Return the comment together with its generated primary key.
    return {**data, "id": last_record_id}


@router.get(
    "/comment/{post_id}/comment",
    response_model=list[Comment],
)
async def get_comments_on_post(post_id: int):
    """Return all comments associated with a specific post."""

    # Restrict the result to comments whose foreign key matches the post ID.
    query = comment_table.select().where(comment_table.c.post_id == post_id)

    return await database.fetch_all(query)


@router.get(
    "/post/{post_id}",
    response_model=UserPostWithComments,
)
async def get_post_with_comments(post_id: int):
    """Return a post together with all of its comments."""

    post = await find_post(post_id)

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found",
        )

    # Build the nested structure expected by UserPostWithComments.
    return {
        "post": post,
        "comments": await get_comments_on_post(post_id),
    }
