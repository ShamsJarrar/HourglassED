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
    proposed_events: Annotated[List[Union[EventCreate, createSeriesWithEvents]]] = []


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]	  # chat history
    user_input: str
    user_feedback: Optional[str]
    proposed_events: Annotated[List[EventCreate | createSeriesWithEvents], add]
    answer: str
    calendar: Annotated[List[EventResponse | RecurrenceSeriesResponse], add]
    max_tool_calls: int
    status: Literal['approved', 'skip', 'feedback']
    access_token: Optional[str]
