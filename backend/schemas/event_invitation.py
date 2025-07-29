from pydantic import BaseModel
from datetime import datetime
from models.event_invitation import EventInvitationStatus


class EventInvitationCreate(BaseModel):
    event_id: int
    invited_user_id: int


class EventInvitationResponse(BaseModel):
    invitation_id: int
    event_id: int
    invited_user_id: int
    status: EventInvitationStatus
    created_at: datetime

    class Config:
        from_attributes = True
