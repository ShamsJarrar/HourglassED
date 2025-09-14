from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from models.agent_proposal import AgentProposalType, AgentProposalStatus



class AgentUserPrefsBase(BaseModel):
    timezone: str = "Asia/Riyadh"
    study_windows: Optional[list[dict[str, Any]]] = None
    no_go_windows: Optional[list[dict[str, Any]]] = None
    session_len_m: int = 90
    buffer_min: int = 10
    naming_rules: Optional[dict[str, Any]] = None         
    course_prefs: Optional[dict[str, Any]] = None


class AgentUserPrefsCreate(AgentUserPrefsBase):
    pass


class AgentUserPrefsResponse(AgentUserPrefsBase):
    user_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentUserPrefsUpdate(BaseModel):
    timezone: Optional[str] = None
    study_windows: Optional[list[dict[str, Any]]] = None
    no_go_windows: Optional[list[dict[str, Any]]] = None
    session_len_m: Optional[int] = None
    buffer_min: Optional[int] = None
    naming_rules: Optional[list[dict[str, Any]]] = None
    course_prefs: Optional[list[dict[str, Any]]] = None




class AgentProposalBase(BaseModel):
    proposal_type: AgentProposalType
    target_event_id: Optional[int] = None
    payload_json: dict[str, Any]
    diff_json: dict[str, Any]
    reasoning_summary: str
    status: AgentProposalStatus = AgentProposalStatus.pending
    expires_at: datetime


class AgentProposalCreate(AgentProposalBase):
    pass


class AgentProposalResponse(AgentProposalBase):
    proposal_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentProposalUpdate(BaseModel):
    status: Optional[AgentProposalStatus] = None
    expires_at: Optional[datetime] = None




class AgentAuditLogBase(BaseModel):
    user_id: int
    proposal_id: Optional[int] = None
    event: str
    payload_json: Optional[dict[str, Any]] = None


class AgentAuditLogCreate(AgentAuditLogBase):
    pass


class AgentAuditLogResponse(AgentAuditLogBase):
    log_id: int
    created_at: datetime

    class Config:
        from_attributes = True
