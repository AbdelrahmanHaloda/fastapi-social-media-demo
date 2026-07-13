from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserPostIn(BaseModel):
    Body: str

class UserPost(UserPostIn):
    id: int

# database
post_table = {}

@app.post("/post", response_model = UserPost)
async def create_post(post: UserPostIn):
    data = post.dict()
    lastPostId = len(post_table)
    new_post = {**data, "id": lastPostId + 1}
    post_table[lastPostId] = new_post
    return new_post


@app.get("/posts", response_model = list[UserPost])
async def get_posts():
    return list(post_table.values())
