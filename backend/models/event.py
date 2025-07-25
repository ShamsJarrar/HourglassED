from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Event(Base):
    __tablename__ = "events"
    
    event_id = Column(Integer, primary_key=True)
    event_type = Column(Integer, ForeignKey("event_classes.class_id", ondelete="RESTRICT"), nullable=False)
    header = Column(String(255))
    title = Column(String(255))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    recurrence_pattern = Column(String(255))
    color = Column(String(20), default="#FFD700")
    notes = Column(Text)
    linked_event_id = Column(Integer, ForeignKey("events.event_id", ondelete="SET NULL"))
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    event_class = relationship("EventClass", backref="events")
    user = relationship("User", backref="events")
    linked_event = relationship("Event", remote_side=[event_id])