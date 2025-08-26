from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Friend(Base):
    __tablename__ = "friends"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    friend_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    
    user = relationship("User", foreign_keys=[user_id], passive_deletes=True)
    friend_user = relationship("User", foreign_keys=[friend_id], passive_deletes=True)