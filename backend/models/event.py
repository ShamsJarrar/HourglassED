from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Event(Base):
    __tablename__ = "events"
    
    event_id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Integer, ForeignKey("event_classes.class_id", ondelete="RESTRICT"), nullable=False)
    header = Column(String(255))
    title = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    color = Column(String(20), default="#FFD700")
    notes = Column(Text)
    linked_event_id = Column(Integer, ForeignKey("events.event_id", ondelete="SET NULL"))
    recurring_event_id = Column(Integer, ForeignKey("events.event_id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    event_class = relationship("EventClass", backref="events", passive_deletes=True)
    user = relationship("User", backref="events", foreign_keys=[user_id], passive_deletes=True)
    linked_event = relationship("Event", remote_side=[event_id], foreign_keys=[linked_event_id], passive_deletes=True)
    invitations = relationship("EventInvitation", back_populates="event", passive_deletes=True, cascade="all, delete-orphan")
    parent_recurring_event = relationship("Event", remote_side=[event_id], foreign_keys=[recurring_event_id], backref="recurring_events", passive_deletes=True)