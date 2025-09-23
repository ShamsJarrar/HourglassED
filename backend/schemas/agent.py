from pydantic import BaseModel
from typing import Optional, Any, Literal
from datetime import datetime
from models.agent_proposal import AgentProposalType, AgentProposalStatus



# Agent User Preferences
class AgentUserPrefsBase(BaseModel):
    timezone: str = "UTC"
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
    naming_rules: Optional[dict[str, Any]] = None
    course_prefs: Optional[dict[str, Any]] = None




# Agent Proposals
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




# Agent Audit Logs
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



# Request bodies for agent proposals
class EventDraft(BaseModel):
    event_type: str
    title: str
    start_time: datetime
    end_time: datetime
    timezone: str = 'UTC'
    header: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None
    series_id: Optional[int] = None
    recurrence_pattern: Optional[str] = None


class ProposeCreateRequest(BaseModel):
    draft: EventDraft
    reasoning_summary: str


UpdateScope = Literal["occurrence", "series"]
class UpdateDraft(BaseModel):
    update_scope: UpdateScope = "occurrence"
    event_id: int
    event_type: Optional[str] = None
    title: Optional[str] = None
    header: Optional[str] = None
    notes: Optional[str] = None
    color: Optional[str] = None
    timezone: Optional[str] = None
    start_time: Optional[datetime] = None      
    end_time: Optional[datetime] = None        
    recurrence_pattern: Optional[str] = None   
    series_id: Optional[int] = None


class ProposeUpdateRequest(BaseModel):
    draft: UpdateDraft
    reasoning_summary: str


DeleteScope = Literal["occurrence", "series"]
class DeleteDraft(BaseModel):
    delete_scope: DeleteScope = "occurrence"
    event_id: int
    series_id: Optional[int] = None


class ProposeDeleteRequest(BaseModel):
    draft: DeleteDraft
    reasoning_summary: str