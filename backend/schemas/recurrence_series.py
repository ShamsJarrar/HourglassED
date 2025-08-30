from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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


class RecurrenceSeriesUpdate(BaseModel):
    recurrence_pattern: Optional[str] = None
    recurrence_end: Optional[datetime] = None