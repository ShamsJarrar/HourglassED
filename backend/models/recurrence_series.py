from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class RecurrenceSeries(Base):
    __tablename__ = "recurrence_series"

    series_id = Column(Integer, primary_key=True, index=True)
    recurrence_pattern = Column(String(255), nullable=False)
    recurrence_end = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="recurrence_series", foreign_keys=[user_id], passive_deletes=True)
    events = relationship("Event", back_populates="series", cascade="all, delete-orphan")