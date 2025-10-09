from pydantic import BaseModel
from typing import Literal, Optional, List
from schemas.event import EventCreate
from agent.state import createSeriesWithEvents


class InitialRequest(BaseModel):
    user_input: str
    max_tool_calls: Optional[int] = 4
    client_now_iso: Optional[str] = None
    client_timezone: Optional[str] = None


class ResumeRequest(BaseModel):
    thread_id: str
    status: Literal['approved', 'skip', 'feedback']
    user_feedback: Optional[str] = None


class AgentResponse(BaseModel):
    thread_id: str
    run_state: Literal['user_feedback', 'finished']
    answer: str
    proposed_events: Optional[List[EventCreate | createSeriesWithEvents]] = None