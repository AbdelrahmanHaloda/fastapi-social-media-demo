from fastapi import APIRouter

from app.models.post import UserPost, UserPostIn

router = APIRouter()


# database
post_table = {}


@router.post("/post", response_model=UserPost)
async def create_post(post: UserPostIn):
    data = post.dict()
    lastPostId = len(post_table)
    new_post = {**data, "id": lastPostId + 1}
    post_table[lastPostId] = new_post
    return new_post


@router.get("/posts", response_model=list[UserPost])
async def get_posts():
    return list(post_table.values())
