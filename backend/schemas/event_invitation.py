from pydantic import BaseModel
from datetime import datetime
from models.event_invitation import EventInvitationStatus
from schemas.event import EventResponseWithOwnerEmail
from typing import Optional


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


class EventInvitationResponseUpdate(BaseModel):
    invitation_id: int
    response: EventInvitationStatus


class EventUserEmail(BaseModel):
    email: str

    class Config:
        from_attributes = True


class EventInvitationWithEvent(BaseModel):
    invitation_id: int
    status: EventInvitationStatus
    created_at: datetime
    event: EventResponseWithOwnerEmail
    invited_user: Optional[EventUserEmail] = None

    class Config:
        from_attributes = True


class ParticipantsResponse(BaseModel):
    user_name: str
    user_email: str

    class Config:
        from_attributes = True