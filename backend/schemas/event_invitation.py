from pydantic import BaseModel
from datetime import datetime
from models.event_invitation import EventInvitationStatus
from schemas.event import EventResponseWithOwnerEmail


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


class EventInvitationWithEvent(BaseModel):
    invitation_id: int
    status: EventInvitationStatus
    created_at: datetime
    event: EventResponseWithOwnerEmail

    class Config:
        from_attributes = True