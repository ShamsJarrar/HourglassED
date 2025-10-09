from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing import TypedDict, Annotated, Sequence, Optional, List, Literal, Union
from schemas.event import EventCreate, EventResponse
from schemas.recurrence_series import RecurrenceSeriesCreate, RecurrenceSeriesResponse
from pydantic import BaseModel
from operator import add


class createSeriesWithEvents(BaseModel):
    recurrence: RecurrenceSeriesCreate
    event: EventCreate


class OrganizerReply(BaseModel):
    answer: str
    # Do NOT accumulate proposed events across runs; each reply overwrites
    proposed_events: List[Union[EventCreate, createSeriesWithEvents]] = []


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]	  # chat history
    user_input: str
    user_feedback: Optional[str]
    # Clear and replace on each validated model output, not reduce/add
    proposed_events: List[EventCreate | createSeriesWithEvents]
    answer: str
    calendar: Annotated[List[EventResponse | RecurrenceSeriesResponse], add]
    max_tool_calls: int
    tool_calls_used: int
    status: Literal['approved', 'skip', 'feedback']
    access_token: Optional[str]
    client_now_iso: Optional[str]
    client_timezone: Optional[str]
