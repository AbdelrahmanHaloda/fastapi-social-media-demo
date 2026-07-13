from pydantic import BaseModel


class UserPostIn(BaseModel):
    Body: str

class UserPost(UserPostIn):
    id: int
