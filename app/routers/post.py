from fastapi import APIRouter, HTTPException

from app.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)

router = APIRouter()


# database
post_table = {}
comment_table = {}

""" Find a post by ID """
def find_post(post_id: int):
    return post_table.get(post_id)


""" Create a new post """
@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(post: UserPostIn):
    data = post.dict()
    lastPostId = len(post_table)
    new_post = {**data, "id": lastPostId + 1}
    post_table[lastPostId + 1] = new_post
    return new_post

""" Get all posts """
@router.get("/posts", response_model=list[UserPost])
async def get_posts():
    return list(post_table.values())

""" Create a new comment """
@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(comment: CommentIn):

    post = find_post(comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    data = comment.dict()
    lastCommentId = len(comment_table)
    new_comment = {**data, "id": lastCommentId + 1}
    comment_table[lastCommentId] = new_comment
    return new_comment

""" Get all comments for a specific post """
@router.get("/comment/{post_id}/comment", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    return [
        comment for comment in comment_table.values() if comment["post_id"] == post_id
        ]

""" Get a post along with its comments """
@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    post = find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    
    return {"post": post, "comments": await get_comments_on_post(post_id)}