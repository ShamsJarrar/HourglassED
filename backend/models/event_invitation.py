from sqlalchemy import Column, Integer, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base
import enum

class EventInvitationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class EventInvitation(Base):
    __tablename__ = "event_invitations"

    invitation_id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False)
    invited_user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(EventInvitationStatus), default=EventInvitationStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invited_user = relationship("User")
    event = relationship("Event", backref = 'invitations', foreign_keys=[event_id])