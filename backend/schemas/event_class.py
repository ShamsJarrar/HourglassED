from pydantic import BaseModel
from typing import Optional


class EventClassCreate(BaseModel):
    class_name: str


class EventClassResponse(BaseModel):
    class_id: int
    class_name: str
    is_builtin: bool
    created_by: Optional[int]

    class Config:
        from_attributes = True

