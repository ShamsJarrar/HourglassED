from pydantic import BaseModel


class FriendResponse(BaseModel):
    friend_id: int
    friend_name: str
    friend_email: str

    class Config:
        from_attributes = True