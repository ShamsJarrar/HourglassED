"""
Organizer node: 
- Converts (intent, slots, prefs, calendar) into drafts for proposal:
    Draft = {"action": "create" | "update" | "delete", "body": {...schema...}}
- For 'ask' intent, produce immediate answer (no drafts).
- For 'plan' intent, if LLM produces no drafts, fallback to greedy planner
  which uses availability and prefs.

Inputs in state:
    intent: "ask" | "add" | "plan" | "other"
    slots: Slots
    prefs: Prefs
    calendar: CalendarSnapshot
      - events: List[dict]
      - availability: Dict with keys {"timezone": str, "busy": List[dict], "free": List[dict]}
                                                                            dict: {"start": start, "end": end}

Outputs in state:
    drafts: list[Draft]
    answer: Optional[str]
"""


from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from ..state import AgentState, Slots, Prefs, CalendarSnapshot, Draft
from ._llm import chat_json


ORGANIZER_PROMPT = """
You are the Organizer for a student-oriented calender agent.

Your job:
- Turn the user's intent+slots+prefs into concrete drafts for proposals.
- A draft is one of:
  - CREATE:  {"action":"create", "body": {EventDraft fields}}
  - UPDATE:  {"action":"update", "body": {UpdateDraft fields}}
  - DELETE:  {"action":"delete", "body": {DeleteDraft fields}}

Schemas
- CREATE body (EventDraft fields):
  {
    "event_type": str,  // backend maps string to class_id
    "title": str,
    "start_time": ISO-8601,
    "end_time": ISO-8601,
    "timezone": str (default 'UTC' if unknown),
    "header": str | null,
    "color": str | null,
    "notes": str | null,
    "series_id": int | null,
    "recurrence_pattern": str | null
  }

- UPDATE body (UpdateDraft fields):
  {
    "update_scope": "occurrence" | "series",
    "event_id": int,
    "event_type": str | null,
    "title": str | null,
    "header": str | null,
    "notes": str | null,
    "color": str | null,
    "timezone": str | null,
    "start_time": ISO-8601 | null,
    "end_time": ISO-8601 | null,
    "recurrence_pattern": str | null,
    "series_id": int | null,
    "recurrence_end": ISO-8601 | null
  }

- DELETE body (DeleteDraft fields):
  {
    "delete_scope": "occurrence" | "series",
    "event_id": int,
    "series_id": int | null
  }

Event types:
- Prefer these built-in categories when appropriate:
  exam, subject, study_session, work, personal, extracurricular
- You may also see common types like: focus, meeting, errand, workout, class, break.

Guidance:
- Use ISO-8601 for all date/time fields; do not invent a time if the user didn't give one.
- Use prefs when helpful (timezone, session_len_m=90 default, buffer_min=10 default)
- For 'ask' intent: produce NO drafts and include a short 'answer' summary of what the user asked (1-2 lines).
- For 'plan' intent: if the user asked to plan study sessions and didn't specify exact times, propose multiple create drafts distributed across available times
   respecting session_len_m and buffer_min. Prefer evenings is the user mentioned evenings, otherwise spread reasonably. Use the given event_type/title if present, other pick sensible defaults.
   e.g. Header: Study, title: <topic>

Output JSON:
{
    "drafts": [...],
    "answer": "..."  // optional short summary for 'ask'
}
"""


def _get_timezone(prefs: Prefs, slots: Slots, availability: Dict[str, Any]) -> str:
    return slots.get("timezone") or prefs.get("timezone") or availability.get("timezone") or "UTC"

def _iso(dt: datetime) -> str:
    return dt.isoformat()

def _parse_iso(s: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def _coerce_free_blocks(avail: Any) -> List[Dict[str, Any]]:
    """
    Accepts either:
      - Dict with keys {"free": List[dict], "busy": List[dict], "timezone": str} (preferred)
      - List[dict] of blocks (legacy)
    Returns a list of {start, end, ...} blocks from the 'free' portion.
    """
    if isinstance(avail, dict) and isinstance(avail.get("free"), list):
        return avail["free"]
    if isinstance(avail, list):
        return avail
    return []
    

def _greedy_planner(
    title: str,
    event_type: str,
    free_blocks: List[Dict[str, Any]],
    hours_needed: float,
    session_len_m: Optional[int],
    buffer_min: Optional[int],
    timezone_name: str,
) -> List[Draft]:
    """
    Fallback greedy planner:
    - Chops free windows into sessions of session_len_m with buffer_min between them.
    - Stop when allocated ~hours_needed.
    """

    session = max(int(session_len_m or 90), 20)
    buffer_min = max(int(buffer_min or 10), 0)
    remaining_min = max(int(hours_needed * 60), session)

    drafts: List[Draft] = []

    for block in free_blocks:
        if remaining_min <= 0:
            break
        
        start = _parse_iso(str(block.get("start")))
        end = _parse_iso(str(block.get("end")))
        if not start or not end or end <= start:
            continue
    
    cursor = start
    while cursor + timedelta(minutes=session) <= end and remaining_min > 0:
        start = cursor
        end = start + timedelta(minutes=session)
        drafts.append(Draft(
            action="create",
            body={
                "event_type": event_type,
                "title": f"{title}",
                "start_time": _iso(start),
                "end_time": _iso(end),
                "timezone": timezone_name,
                "header": None,
                "color": None,
                "notes": None,
                "series_id": None,
                "recurrence_pattern": None
            }
        ))
        remaining_min -= session
        cursor = end + timedelta(minutes=buffer_min)
    
    return drafts



async def organizer(state: AgentState) -> AgentState:
    intent = state.get("intent", "other")
    slots: Slots = state.get("slots", {}) or {}
    prefs: Prefs = state.get("prefs", {}) or {}
    calendar: CalendarSnapshot = state.get("calendar", {}) or {}

    availability: Dict[str, Any] = calendar.get("availability", {}) or {}
    free_blocks: List[Dict[str, Any]] = _coerce_free_blocks(availability)

    events_list: List[Dict[str, Any]] = calendar.get("events", []) or []
    events_summary = {
        "count": len(events_list),
        "sample_titles": [e.get("title") for e in events_list[:5] if isinstance(e, dict)]
    }

    model_input = {
        "intent": intent,
        "slots": slots,
        "prefs": prefs,
        "calendar": {
            "events_summary": events_summary,
            "availability": {
                "timezone": availability.get("timezone"),
                "free_count": len(free_blocks),
                "busy_count": len(availability.get("busy", []) if isinstance(availability, dict) else [])
            }
        }
    }

    response = await chat_json(ORGANIZER_PROMPT, str(model_input), "organizer_output") or {}
    drafts_input: List[Draft] = response.get("drafts", []) or []


    if intent == "ask":
        if response.get("answer"):
            state["answer"] = response.get("answer")
        state["drafts"] = drafts_input
        return state
    

    drafts: List[Draft] = list(drafts_input)
    if intent == "plan" and not drafts:
        event_type = (slots.get("event_type") or "focus").lower()
        title = slots.get("title") or "Plan"
        hours_needed = float(slots.get("hours_needed") or 3.0)
        session_len_m = prefs.get("session_len_m") or 90
        buffer_min = prefs.get("buffer_min") or 10
        timezone = _get_timezone(prefs, slots, availability)

        drafts = _greedy_planner(
            title=title,
            event_type=event_type,
            free_blocks=free_blocks,
            hours_needed=hours_needed,
            session_len_m=session_len_m,
            buffer_min=buffer_min,
            timezone_name=timezone
        )
    

    normalized_drafts: List[Draft] = []
    for d in drafts:
        action = d.get("action")
        body = dict(d.get("body", {}))
        
        if action in ("create", "update"):
            start = body.get("start_time")
            end = body.get("end_time")
            if start and end:
                start_iso = _parse_iso(start)
                end_iso = _parse_iso(end)
                if not start_iso or not end_iso or end_iso <= start_iso:
                    continue
            body["start_time"] = _iso(start_iso)
            body["end_time"] = _iso(end_iso)
        
        body.setdefault("timezone", _get_timezone(prefs, slots, availability))
        normalized_drafts.append(Draft(
            action=action,
            body=body
        ))
    
    state["drafts"] = normalized_drafts
    if response.get("answer") and not state.get("answer"):
        state["answer"] = response.get("answer")
    return state
