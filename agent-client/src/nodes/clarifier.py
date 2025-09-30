"""
Clarifier node: given the current slots + prefs + user input, ask the user for clarification
using only blocking questions that are needed to proceed.
- Merges any inferred/confirmed value into state.slots.
- Set state.needs_clarification accordingly.
- Optionally place a short question/answer into state.answer foe UI.

Inputs:
    state.user_text (str)
    state.slots (Slots)
    state.prefs (Prefs)
    state.intent (Literal["ask","add","plan","other"])

Outputs:
    state.slots (merged)
    state.needs_clarification (bool)
    state.answer (short question/message to present)
"""

from typing import Any, Dict
from ..state import AgentState, Slots, Prefs
from ._llm import chat_json


CLARIFIER_PROMPT = """
Ypu are the Clarifier for a student-oriented calender agent.
Ask ONLY the minimal, blocking questions that are needed to proceed with the user's intent.

Rules:
- For 'add' (create/update/delete event):
    - If no start_time or end_time is provided: ask for them.
    - If only a date is given (no time), as for the time range (and timezone if missing).
    - If recurrence is applied but not given (example: "every Tuesday"), ask for recurrence_pattern and optional recurrence_end.

- For 'plan':
    - If hours_needed is missing: ask for estimate OR allow you to estimate based on exam difficutly if relevant.
    - If study_windows/no_go_windows/timezone are missing: ask for them briefly.

- For 'ask':
    - If a time window is ambiguous/missing: ask for a concise range (e.g. "this week", "next 14 days").


Keep it concise:
- Return JSON with:
  {
    "still_missing": bool,
    "message": "one short question or confirmation to the user",
    "slots": { ...only fields you are confident about... }
  }

Use only these slot keys if you fill them: 
title, event_type, start_time, end_time, timezone, notes, color, header,
series_id, recurrence_pattern, recurrence_end,
min_block_minutes, title_filter,
exams, hours_needed, study_windows, no_go_windows.

DO NOT INVENT TIMES; if the user provided only a date, leave times blank and set still_missing=true.
Prefer ISO-8601 strings for any dates/times you include.

if a preference is missing BUT does not block the current task, do not ask about it now.
"""


def _merge_slots(base: Slots, add: Dict[str, Any]) -> Slots:
    """
    Guardrail to merge only the allowed slots into the base slots.

    Returns:
        The merged dict.
    """

    if not add:
        return base
    
    allowed = {
        "title","event_type","start_time","end_time","timezone","notes","color","header",
        "series_id","recurrence_pattern","recurrence_end",
        "min_block_minutes","title_filter",
        "exams","hours_needed","study_windows","no_go_windows",
    }
    for key, value in add.items():
        if key in allowed and value is not None:
            base[key] = value
    
    return base


async def clarifier(state: AgentState, config=None) -> AgentState:
    payload = {
        "intent": state.get("intent"),
        "current_slots": state.get("slots", {}),
        "current_prefs": state.get("prefs", {}),
        "user_input": state.get("user_input")
    }

    response = await chat_json(CLARIFIER_PROMPT, str(payload), "clarifier_output") or {}

    current_slots: Slots = dict(state.get("slots", {}))
    merged_slots = _merge_slots(current_slots, response.get("slots", {}))

    state["slots"] = merged_slots
    state["needs_clarification"] = bool(response.get("still_missing", False))
    if response.get("message"):
        state["answer"] = response.get("message")

    return state