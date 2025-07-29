from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class SharedEvent(Base):
    __tablename__ = "shared_events"

    shared_event_id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False)
    shared_with_user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    event = relationship("Event", backref="shared_with")
    user = relationship("User", backref="shared_events")