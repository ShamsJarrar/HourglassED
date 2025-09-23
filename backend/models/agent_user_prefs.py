from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON
from database import Base


class AgentUserPrefs(Base):
    __tablename__ = "agent_user_prefs"

    user_id       = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    timezone      = Column(String(64), nullable=False, default="UTC")
    study_windows = Column(JSON, nullable=True)
    no_go_windows = Column(JSON, nullable=True)
    session_len_m = Column(Integer, nullable=False, server_default=text("90"))
    buffer_min    = Column(Integer, nullable=False, server_default=text("10"))
    naming_rules  = Column(JSON, nullable=True)
    course_prefs  = Column(JSON, nullable=True)
    updated_at    = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        nullable=False,
    )

    user = relationship("User", backref="agent_user_prefs", uselist=False, passive_deletes=True)