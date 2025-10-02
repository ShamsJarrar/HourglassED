"""
Presenter node:
- Summarize pending proposals for the user in natural language.
- Show local + UTC times, action, rationale, and expiry.
- Outputs markdown string in state['answer']

Inputs in state:
    proposals: {"items": [AgentProposalResponse, ...]}
    pending_proposal_id: Optional[int]
    prefs: Prefs                 
    calendar: CalendarSnapshot   

Outputs in state:
    answer: str   # markdown cards text for the UI
"""

from calendar import calendar
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from ..state import AgentState, Prefs, CalendarSnapshot
from ._llm import chat_json
from langchain_core.messages import AIMessage


def _get_timezone(state: AgentState) -> str:
    prefs: Prefs = state.get("prefs") or {}
    calendar: CalendarSnapshot = state.get("calendar") or {}
    availability = calendar.get("availability") or {}
    return prefs.get("timezone") or (availability.get("timezone") if isinstance(availability, dict) else None) or "UTC"


def _parse_iso(s: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def time_info(date: Optional[datetime], timezone: str) -> Tuple[str, str]:
    """ Return (local, utc) time strings """

    if not date:
        return ("-", "-")
    
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    
    try:
        local = date.astimezone(ZoneInfo(timezone))
    except Exception:
        local = date.astimezone(timezone.utc)
        timezone = "UTC"
    
    utc = date.astimezone(timezone.utc)

    def format(dt: datetime) -> str:
        return dt.strftime("%a %d %b %Y, %I:%M %p")
    
    return (f"{format(local)} ({timezone})", f"{format(utc)} (UTC)")


def _get_times(payload: Dict[str, Any]) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    For create: payload['draft'] has start_time/end_time.
    For update: payload['updates'] may have start_time/end_time.
    For delete: no times.
    """
    action = payload.get("action")

    if action == "create":
        draft = payload.get("draft") or {}
        return _parse_iso(draft.get("start_time")), _parse_iso(draft.get("end_time"))
    
    elif action == "update":
        updates = payload.get("updates") or {}
        return _parse_iso(updates.get("start_time")), _parse_iso(updates.get("end_time"))
    
    return (None, None)


def _get_title(payload: Dict[str, Any]) -> str:
    action = payload.get("action")

    if action == "create":
        return (payload.get("draft") or {}).get("title") or "(untitled)"
    
    elif action == "update":
        updates = payload.get("updates") or {}
        return updates.get("title") or "(update event)"
    
    elif action == "delete":
        return f"Delete event #{payload.get('event_id')}"
    
    return "(proposal)"


def _badge(action: str) -> str:
    return {
        "create": "🟢 create",
        "update": "🟡 update",
        "delete": "🔴 delete",
    }.get(action.lower(), action or "proposal")


def _card(proposal: Dict[str, Any], timezone: str) -> str:
    payload = proposal.get("payload_json") or {}
    action = str(payload.get("action") or "").lower()
    title = _get_title(payload)
    start, end = _get_times(payload)
    local_start, utc_start = time_info(start, timezone)
    local_end, utc_end = time_info(end, timezone)
    reason = proposal.get("reasoning_summary") or ""
    expires = _parse_iso(proposal.get("expires_at"))
    exp_local, exp_utc = time_info(expires, timezone)
    pending_proposal_id = proposal.get("proposal_id")

    lines = []
    lines.append(f"**{_badge(action)}** · **{title}**  \n`proposal_id: {pending_proposal_id}`")
    if start and end:
        lines.append(f"- **When (local)**: {local_start} → {local_end}")
        lines.append(f"- **When (UTC)**:   {utc_start} → {utc_end}")
    elif action == "delete":
        lines.append(f"- **Scope**: {payload.get('delete_scope', 'occurrence')}")
    lines.append(f"- **Why**: {reason or '—'}")
    lines.append(f"- **Expires**: {exp_local} / {exp_utc}")
    return "\n".join(lines)



async def presenter(state: AgentState, config=None) -> AgentState:
    intent = (state.get("intent") or "").lower()
    # ASK Intent
    if intent == "ask":
        user_input = state.get("user_input") or ""
        calender = state.get("calendar") or {}

        PROMPT = f"""
        You are a helpful scheduling assistant.

        The user will ask a question about their calendar.
        You are given calendar context below:
        {calender}

        Please answer the question directly in natural language.
        - If the user asked about availability, summarize busy/free slots.
        - If the user asked about events, list their header, titles, and times.
        - Be concise but clear.

        Return STRICT JSON:
        {{
            "text": str
        }}
        """

        response = await chat_json(PROMPT, user_input, history=state.get("history") or [])
        msgs = list(state.get("messages", []))
        msgs.append(AIMessage(content=str(response), name="presenter"))
        state["messages"] = msgs

        state["answer"] = response.get("text") if isinstance(response, dict) else str(response)
        return state
    
    if intent == "other":
        user_input = state.get("user_input") or ""
        calender = state.get("calendar") or {}

        PROMPT = f"""
        You are a helpful scheduling assistant.

        The user will asked a question that could be related to their calendar,
        but not necessarily about their calendar.

        Here is some calendar context if you need:
        {calender}

        Do you your best to answer the question in natural language.

        Return STRICT JSON:
        {{
            "text": str
        }}
        """
        response = await chat_json(PROMPT, user_input, history=state.get("history") or [])
        msgs = list(state.get("messages", []))
        msgs.append(AIMessage(content=str(response), name="presenter"))
        state["messages"] = msgs

        state["answer"] = response.get("text") if isinstance(response, dict) else str(response)
        return state



    # ADD/PLAN/OTHER Intent
    proposals =  state.get("proposals") or {}                               # {"items": [AgentProposalResponse (dict), ...]}
    proposals_list: List[Dict[str, Any]] = proposals.get("items") or []     # [AgentProposalResponse (dict), ...]

    if not proposals_list:
        state["answer"] = state.get("answer") or "No proposals to present"
        return state
    
    timezone = _get_timezone(state)
    header = f"### Pending proposals ({len(proposals_list)})\n"
    cards = []
    for proposal in proposals_list:
        try:
            cards.append(_card(proposal, timezone))
        except Exception:
            pending_proposal_id = proposal.get("proposal_id", "?")
            cards.append(f"**proposal #{pending_proposal_id}** (could not be parsed)")
    
    md = header + "\n\n--\n\n".join(cards)

    state["answer"] = md
    return state
