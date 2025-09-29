from typing import TypedDict, List, Dict, Literal, Any, Optional


Intent = Literal["ask", "add", "plan", "other"]
#   ask  : user asks about events/availability/status
#   add  : user wants to add/update/delete a specific event
#   plan : user wants a study plan/ organizational plan
#   other: fallback / unknown


# used by planner and clarifier nodes
class Slots(TypedDict, total=False):
    # Event fields
    title: str
    event_type: str               
    start_time: str               # ISO string
    end_time: str                 # ISO string
    timezone: str                 
    notes: str
    color: str
    header: str

    # Recurrence fields
    series_id: int
    recurrence_pattern: str       
    recurrence_end: str           # ISO string

    # Query filters
    min_block_minutes: int
    title_filter: str

    # Planning fields
    exams: List[Dict[str, Any]]   # [{"title": "...", "date": "ISO", "difficulty": 1..5}, ...]
    hours_needed: float           # total hours required across plan
    study_windows: List[Dict[str, Any]]  # constraints from prefs or user
    no_go_windows: List[Dict[str, Any]]  # times to avoid


class Prefs(TypedDict, total=False):
    timezone: str
    study_windows: List[Dict[str, Any]]
    no_go_windows: List[Dict[str, Any]]
    session_len_m: int
    buffer_min: int
    naming_rules: Dict[str, Any]
    course_prefs: Dict[str, Any]
    user_id: int
    updated_at: str  # ISO string


DraftAction = Literal["create", "update", "delete"]

# Used for /agent/propose/*
class Draft(TypedDict, total=False):
    action: DraftAction
    body: Dict[str, Any]        # matches backend schemas


# Review output
class Review(TypedDict, total=False):
    issues: List[str]         # detected problems in draft like overlaps
    suggestions: List[str]    
    score: float               # 0..1 quality score



class CalendarSnapshot(TypedDict, total=False):
    events: List[Dict[str, Any]]              # from agent.list_eventd
    availability: List[Dict[str, Any]]         # from agent.list_availability



class Proposals(TypedDict, total=False):
    items: List[Dict[str, Any]]            # from agent.propose_*



class AgentState(TypedDict, total=False):
    user_input: str

    intent: Intent
    slots: Slots
    needs_clarification: bool

    calendar: CalendarSnapshot
    prefs: Prefs

    drafts: List[Draft]
    review: Review

    proposals: Proposals
    pending_proposal_id: Optional[int]

    answer: Optional[str]



def initial_state(user_input: str) -> AgentState:
    return AgentState(
        user_input=user_input,
        intent="other",
        slots=Slots(),
        needs_clarification=False,
        calendar=CalendarSnapshot(),
        prefs=Prefs(),
        drafts=[],
        review=Review(issues=[], suggestions=[], score=0),
        proposals=Proposals(items=[]),
        pending_proposal_id=None,
        answer=None
    )
