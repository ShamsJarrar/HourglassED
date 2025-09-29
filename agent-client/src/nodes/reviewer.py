"""
Reviewer node:
- Does some checks like invalid times, reversed windows, and duplicate drafts
- Then refined drafts are passed to LLM to be reviewed for issues and suggestions

Inputs in state:
    drafts: List[Draft]       
    prefs: Prefs
    calendar: CalendarSnapshot
      - events: List[dict]
      - availability: Dict with keys {"timezone": str, "busy": List[dict], "free": List[dict]}
                                                                            dict: {"start": start, "end": end}

Outputs in state:
    drafts: List[Draft]        # possibly refined     
    review: Review             {issues: [...], suggestions: [...], score: float}
"""


from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from ..state import AgentState, Slots, Prefs, CalendarSnapshot, Draft, Review
from ._llm import chat_json


REVIEWER_PROMPT = """
You are the Reviewer for a student-oriented calender agent.
Given user prefs, calendar context, and proposed drafts, evaluate the quality and
optionally refine drafts.

Goals:
- Detect and explain conflicts (overlaps with existing/busy windows), back-to-backs with too-small buffers,
  unreasonable late-night sessions, overloaded days, broken recurrences, etc.
- If improvements are obvious, produce refined drafts (keep schema) that reduce issues with minimal changes.
- Provide concise, actionable suggestions for the user (1-3 lines).
- Provide an overall quality score from 0.0 to 1.0.

Schemas:
Draft = {"action": "create"|"update"|"delete", "body": {...}}

CREATE body:
  {"event_type": str, "title": str, "start_time": ISO-8601, "end_time": ISO-8601,
   "timezone": str, "header": str|null, "color": str|null, "notes": str|null,
   "series_id": int|null, "recurrence_pattern": str|null}

UPDATE body:
  {"update_scope": "occurrence"|"series", "event_id": int, "event_type": str|null,
   "title": str|null, "header": str|null, "notes": str|null, "color": str|null,
   "timezone": str|null, "start_time": ISO-8601|null, "end_time": ISO-8601|null,
   "recurrence_pattern": str|null, "series_id": int|null, "recurrence_end": ISO-8601|null}

DELETE body:
  {"delete_scope": "occurrence"|"series", "event_id": int, "series_id": int|null}

Calendar availability shape: {"timezone": str, "busy": [...], "free": [...]}

Prefs: timezone, session_len_m (default 90), buffer_min (default 10), study/no-go windows.


Return STRICT JSON:
{
  "issues": [ "..." ],
  "suggestions": [ "..." ],
  "score": 0.0-1.0,
  "revised_drafts": [ Draft, ... ]   // may be empty; if empty, keep originals
}
"""




def _parse_iso(s: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def _is_valid_window(draft: Draft) -> bool:
    """Create or update draft must have valid start/end times"""
    action = draft.get("action")
    if action not in ("create", "update"):
        return True
    
    body = draft.get("body") or {}
    start, end  = body.get("start_time"), body.get("end_time")

    if not start or not end:
        return False
    
    start, end = _parse_iso(start), _parse_iso(end)
    return bool(start and end and end > start)

def _remove_duplicate_drafts(drafts: List[Draft]) -> List[Draft]:
    seen = set()
    output: List[Draft] = []
    for d in drafts:
        key = (d.get("action"), tuple(sorted((d.get("body") or {}).items())))
        if key in seen:
            continue
        seen.add(key)
        output.append(d)
    return output



async def reviewer(state: AgentState) -> AgentState:
    drafts: List[Draft] = list(state.get("drafts") or [])
    prefs: Prefs = state.get("prefs") or {}
    calendar: CalendarSnapshot = state.get("calendar") or {}

    refined_drafts = [d for d in _remove_duplicate_drafts(drafts) if _is_valid_window(d)]
    
    payload = {
        "prefs": prefs,
        "calendar": calendar,
        "drafts": refined_drafts
    }
    response = await chat_json(REVIEWER_PROMPT, str(payload), "reviewer") or {}

    issues = [str(x) for x in (response.get("issues") or [])][:12]
    suggestions = [str(x) for x in (response.get("suggestions") or [])][:6]
    try:
        score = float(response.get("score") or 0.0)
    except Exception:
        score = 0.0
    
    revised_drafts = response.get("revised_drafts")
    if isinstance(revised_drafts, list) and revised_drafts:
        drafts_output = revised_drafts
    else:
        drafts_output = refined_drafts
    

    refined_drafts_output = [d for d in _remove_duplicate_drafts(drafts_output) if _is_valid_window(d)]

    state["drafts"] = refined_drafts_output
    state["review"] = Review(
        issues=issues,
        suggestions=suggestions,
        score=score
    )
    return state
