from pydantic import BaseModel


class SharedEventCreate(BaseModel):
    event_id: int
    shared_with_user_id: int


class SharedEventResponse(BaseModel):
    shared_event_id: int
    event_id: int
    shared_with_user_id: int

    class Config:
        from_attributes = True