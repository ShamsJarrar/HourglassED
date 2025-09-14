from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, TIMESTAMP, text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON
from database import Base


class AgentAuditLog(Base):
    __tablename__ = "agent_audit_log"

    log_id       = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    proposal_id  = Column(BigInteger, ForeignKey("agent_proposals.proposal_id", ondelete="SET NULL"), nullable=True, index=True)
    event        = Column(String(120), nullable=False)
    payload_json = Column(JSON, nullable=True)
    created_at   = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    user     = relationship("User", foreign_keys=[user_id], passive_deletes=True)
    proposal = relationship("AgentProposal", foreign_keys=[proposal_id], passive_deletes=True)

    __table_args__ = (
        Index("idx_audit_user_created", "user_id", "created_at"),
    )