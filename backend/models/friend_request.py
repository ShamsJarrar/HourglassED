from sqlalchemy import Column, Integer, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base
import enum

class FriendRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    request_id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(FriendRequestStatus), default=FriendRequestStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sender = relationship("User", foreign_keys=[sender_id], passive_deletes=True)
    receiver = relationship("User", foreign_keys=[receiver_id], passive_deletes=True)