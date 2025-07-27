from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EventCreate(BaseModel):
    event_type: int
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

    class Config:
        from_attributes = True
    

class EventUpdate(BaseModel):
    event_type: Optional[int] = None
    header: Optional[str] = None
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    recurrence_pattern: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None
    linked_event_id: Optional[int] = None