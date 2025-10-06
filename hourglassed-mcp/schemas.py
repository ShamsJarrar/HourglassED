from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EventBase(BaseModel):
    event_type: str                      # event_type is inputted as a string, and then normalized to an int in the backend
    header: Optional[str] = None
    title: str
    start_time: datetime
    end_time: datetime
    color: Optional[str] = None
    notes: Optional[str] = None
    series_id: Optional[int] = None
    is_exception: Optional[bool] = False
    timezone: str = "UTC"


class EventCreate(EventBase):
    pass


class EventResponse(EventBase):
    event_id: int
    user_id: int
    event_type: int

    class Config:
        from_attributes = True


class RecurrenceSeriesBase(BaseModel):
    recurrence_pattern: str
    recurrence_end: Optional[datetime] = None


class RecurrenceSeriesCreate(RecurrenceSeriesBase):
    pass


class RecurrenceSeriesResponse(RecurrenceSeriesBase):
    series_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True