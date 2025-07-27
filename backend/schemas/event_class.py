from pydantic import BaseModel


class EventClassCreate(BaseModel):
    class_name: str


class EventClassResponse(BaseModel):
    class_id: int
    class_name: str
    is_builtin: bool

    class Config:
        from_attributes = True

