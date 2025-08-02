from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EventCreate(BaseModel):
    event_type: str
    header: Optional[str] = None
    title: str
    start_time: datetime
    end_time: datetime
    recurrence_pattern: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None
    linked_event_id: Optional[int] = None


class EventResponse(EventCreate):
    event_id: int
    user_id: int
    event_type: int

    class Config:
        from_attributes = True
    

class EventUpdate(BaseModel):
    event_type: Optional[str] = None
    header: Optional[str] = None
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    recurrence_pattern: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None
    linked_event_id: Optional[int] = None


class EventOwnerEmail(BaseModel):
    email: str

    class Config:
        from_attributes = True


class EventResponseWithOwnerEmail(EventCreate):
    event_id: int
    event_type: int
    user: EventOwnerEmail

    class Config:
        from_attributes = True