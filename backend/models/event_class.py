from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class EventClass(Base):
    __tablename__ = "event_classes"

    class_id = Column(Integer, primary_key=True)
    class_name = Column(String(255), nullable=False)
    is_builtin = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey('users.user_id', ondelete="SET NULL"))

    creator = relationship("User", backref="custom_event_classes", foreign_keys=[created_by], passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("class_name", "created_by", name="unique_class_per_user"),
    )