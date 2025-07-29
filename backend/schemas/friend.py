from pydantic import BaseModel


class FriendResponse(BaseModel):
    user_id: int
    friend_id: int

    class Config:
        from_attributes = True
