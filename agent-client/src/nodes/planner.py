"""
Planner node: understand the input like a human would
- Classify the user's intent: ask, add, plan, other
- Extract slots from the user's input (title, time, etc)
- Decides if more clarification is needed

if llm is not available, fallback heuristic is implemented in _fallback()

Inputs:
    state.user_input (string)

Outputs:
    state.intent (Literal["ask", "add", "plan", "other"])
    state.slots (Slots)
    state.needs_clarification (bool)

"""

from typing import Any, Dict
from datetime import date, timedelta
from ..state import AgentState, Slots, Intent
from ._llm import chat_json


PLANNER_PROMPT = """
You are the Planner for a student-oriented calender agent.
Classify the user's intent and extract slots from the user's input.

Valid intents:
- ask: user asks about events, availability, or status ("what is my schedule tomorrow?")
- add: user wants to add/update/delete a specific event ("add a study session for tomorrow at 3pm", "move my meeting")
- plan: create a schedule/time-block plan across days/weeks ('exam', 'subject', 'study_session', 'work', 'personal', 'extracurricular')
- other: anything else that doesn't fit into the above categories

Return a compact JSON object: {"intent": <str>, "slots": <obj>, "needs_clarification": <bool>}

"slots" should only include the fields that you are confident about:
    title, event_type, start_time, end_time, timezone, notes, color, header,
    series_id, recurrence_pattern, recurrence_end,
    min_block_minutes, title_filter,
    exams (list of {title, date (ISO), difficulty}), hours_needed (float),
    study_windows (list of windows), no_go_windows (list of windows)


Guidance:
- Prefer ISO-8601 formatted dates/times. If the user gives a dat without a time, don't invent time.
  Put only the date as ISO (e.g., "2025-10-20") and set needs_clarification=true
- event_type can be one of these built-in categories:
  exam, subject, study_session, work, personal, extracurricular
  (or other obvious calendar categories such as meeting, workout, etc.)
- Do not hallucinate values. If you are not sure about a field, leave it out and set needs_clarification=true
- For plan requests (time-blocking), include any explicit preferences (e.g., mornings, evenings, weekdays).
- Keep the JSON compact and to the point; do not add extra fields that are not in the schema above.
"""


_CANON = {
    # -------- built-in types ------------
    "exam": {"exam", "test", "quiz"},
    "subject": {"subject", "course subject"},
    "study_session": {"study session", "study", "revision", "revise", "learn"},
    "work": {"work", "job", "office", "project"},
    "personal": {"personal", "dentist", "doctor", "appointment", "appt"},
    "extracurricular": {"extracurricular", "club", "sports team", "society"},
    # -------- extra ----------
    "focus": {"focus", "deep work", "time block", "time-block", "block", "coding"},
    "meeting": {"meeting", "meet", "call", "sync", "standup"},
    "errand": {"errand", "groceries", "shopping", "bank", "dmv"},
    "workout": {"workout", "gym", "run", "running", "swim", "yoga"},
    "class": {"class", "lecture", "lesson"},
    "break": {"break", "rest"},
}


def _fallback(input: str) -> Dict[str, Any]:
    """
    Fallback heuristic for when LLM is not available.
    """

    text = input.lower()
    intent = "other"
    if any(k in text for k in ["plan study", "study plan", "schedule study", "prepare for exam", "revise"]):
        intent = "plan"
    
    elif any(k in text for k in ["add", "create", "schedule", "book", "move", "update", "reschedule", "delete", "cancel"]):
        intent = "add"

    elif any(k in text for k in ["what do i have", "availability", "free time", "free slots", "show my events", "list events"]):
        intent = "ask"
    

    slots: Slots = {}
    if "tomorrow" in text:
        slots["start_time"] = (date.today() + timedelta(days=1)).isoformat()
    
    needs_clarification = intent in ("add", "plan")
    return {"intent": intent, "slots": slots, "needs_clarification": needs_clarification}


def _normalize_event_type(text: str | None) -> str | None:
    if not text:
        return None
    
    text = text.lower().strip()
    if text in _CANON:
        return text
    
    for canon, words in _CANON.items():
        if any(w in text for w in words):
            return canon

    return text


def _normalize_slots(raw_slots: Dict[str, Any]) -> Slots:
    """
    Guardrail to ensure are fields are in the correct field type (int, str, etc), and
    remove any extra fields that the llm added.
    """

    allowed = {
        "title","event_type","start_time","end_time","timezone","notes","color","header",
        "series_id","recurrence_pattern","recurrence_end",
        "min_block_minutes","title_filter",
        "exams","hours_needed","study_windows","no_go_windows",
    }

    slots: Dict[str, Any] = {}
    for key, value in (raw_slots or {}).items():
        if key not in allowed:
            continue

        if key in ("min_block_minutes") and isinstance(value, str) and value.isdigit():
            value = int(value)
        
        if key in ("hours_needed") and isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                continue
        
        slots[key] = value
    
    return slots


async def planner(state: AgentState, config=None) -> AgentState:
    user_input = state.get("user_input") or ""

    try:
        response = await chat_json(PLANNER_PROMPT, user_input, "planner_output")
        intent = response.get("intent", "other")
        needs_clarification = bool(response.get("needs_clarification", False))
        slots = _normalize_slots(response.get("slots", {}))

        event_type = _normalize_event_type(slots.get("event_type"))
        if event_type:
            slots["event_type"] = event_type

        if intent in ("add","plan") and not any(k in slots for k in ("start_time", "end_time", "study_windows", "hours_needed", "exams")):
            needs_clarification = True
        
        state["intent"] = intent
        state["slots"] = slots
        state["needs_clarification"] = needs_clarification
        return state
    
    except Exception as e:
        fallback = _fallback(user_input)
        state["intent"] = fallback["intent"]
        state["slots"] = _normalize_slots(fallback["slots"])
        state["needs_clarification"] = bool(fallback["needs_clarification"])
        return state
