from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class EventClass(Base):
    __tablename__ = "event_classes"

    class_id = Column(Integer, primary_key=True)
    class_name = Column(String(255), unique=True, nullable=False)
    is_builtin = Column(Boolean, default=False)