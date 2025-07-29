from pydantic import BaseModel, EmailStr
from datetime import datetime
from models.friend_request import FriendRequestStatus


class FriendRequestCreate(BaseModel):
    receiver_email: EmailStr


class FriendRequestResponse(BaseModel):
    request_id: int
    sender_id: int
    receiver_id: int
    status: FriendRequestStatus
    created_at: datetime

    class Config:
        from_attributes = True

