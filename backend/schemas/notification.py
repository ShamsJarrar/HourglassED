from pydantic import BaseModel
from datetime import datetime


class NotificationResponse(BaseModel):
    notification_id: int
    user_id: int
    message: str
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True