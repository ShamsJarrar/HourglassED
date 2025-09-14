from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Integer, String, TIMESTAMP, text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON
from database import Base
import enum


class AgentProposalType(str, enum.Enum):
    create_event = "create_event"
    update_event = "update_event"
    delete_event = "delete_event"
    batch_plan = "batch_plan"


class AgentProposalStatus(str, enum.Enum):
    pending = "pending"
    committed = "committed"
    rejected = "rejected"
    expired = "expired"


class AgentProposal(Base):
    __tablename__ = "agent_proposals"

    proposal_id       = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id           = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    proposal_type     = Column(
        Enum(AgentProposalType, name="proposal_type", native_enum=False),  
        nullable=False,
    )
    target_event_id   = Column(Integer, ForeignKey("events.event_id", ondelete="SET NULL"), nullable=True)
    payload_json      = Column(JSON, nullable=False)
    diff_json         = Column(JSON, nullable=False)
    reasoning_summary = Column(String(255), nullable=False)
    status            = Column(
        Enum(AgentProposalStatus, name="proposal_status", native_enum=False),
        nullable=False,
        server_default=text("'pending'"),
    )
    expires_at        = Column(DateTime, nullable=False)

    created_at        = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at        = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        nullable=False,
    )

    user         = relationship("User", foreign_keys=[user_id], passive_deletes=True)
    target_event = relationship("Event", foreign_keys=[target_event_id], passive_deletes=True)

    __table_args__ = (
        Index("idx_agent_proposals_user_status", "user_id", "status"),
        Index("idx_agent_proposals_expires", "expires_at"),
    )