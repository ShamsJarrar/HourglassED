from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
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
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    series_id = Column(Integer, ForeignKey("recurrence_series.series_id", ondelete="CASCADE"), nullable=True)

    # is_exception and timezone are not used for now and are defaulted to False and "UTC"
    is_exception = Column(Boolean, default=False)
    timezone = Column(String(64), default="UTC")

    event_class = relationship("EventClass", backref="events", passive_deletes=True)
    user = relationship("User", backref="events", foreign_keys=[user_id], passive_deletes=True)
    series = relationship("RecurrenceSeries", back_populates="events", foreign_keys=[series_id], passive_deletes=True)
    invitations = relationship("EventInvitation", back_populates="event", passive_deletes=True, cascade="all, delete-orphan")
