from sqlalchemy import Column, Integer, ForeignKey
from database import Base

class Friend(Base):
    __tablename__ = "friends"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    friend_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    