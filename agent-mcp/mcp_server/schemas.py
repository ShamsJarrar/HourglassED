from pydantic import BaseModel
from typing import Optional, Any, Literal
from datetime import datetime
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
    recurrence_end: Optional[datetime] = None


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


class AgentUserPrefsUpdate(BaseModel):
    timezone: Optional[str] = None
    study_windows: Optional[list[dict[str, Any]]] = None
    no_go_windows: Optional[list[dict[str, Any]]] = None
    session_len_m: Optional[int] = None
    buffer_min: Optional[int] = None
    naming_rules: Optional[dict[str, Any]] = None
    course_prefs: Optional[dict[str, Any]] = None
