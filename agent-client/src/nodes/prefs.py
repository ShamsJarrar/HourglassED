"""
Prefs node:
- Ensure prefs exist by calling agent.get_prefs (the backend creates defaults if none exist).
- If user provided prefs in slots (timezone, study/no_go windows), update the prefs through agent.update_prefs.
- Store current prefs into state['prefs']
"""

from typing import Any, Dict
from ..state import AgentState, Prefs
from ..mcp_tools import MCPTools, MCPError
import json



PREF_KEYS = {
    "timezone",
    "study_windows",
    "no_go_windows",
    "session_len_m",
    "buffer_min",
    "naming_rules",
    "course_prefs"
}


def _normalize_prefs(raw_prefs: Dict[str, Any]) -> Prefs:
    """
    Keep only the pref keys from the raw_prefs and basic metadat from backend
    """

    if not raw_prefs:
        return Prefs()
    
    output: Dict[str, Any] = {}
    for key in PREF_KEYS.union({"user_id", "updated_at"}):
        if key in raw_prefs:
            output[key] = raw_prefs[key]
    
    return Prefs(**output)



def _extract_prefs(slots: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pick only the pref keys from the slots that are present to send in update.
    """
    output: Dict[str, Any] = {}
    for key in PREF_KEYS:
        if key in slots and slots[key] is not None:
            output[key] = slots[key]
    
    return output


async def ensure_prefs(state: AgentState, config: Dict[str, Any] | None = None) -> AgentState:
    """
    - Read prefs (GET /agent/prefs) - backend will create defaults if none exist.
    - If slots include pref-like fields, update prefs (PUT /agent/prefs)
    - Read current prefs into state['prefs']
    """
    tools: MCPTools = (config or {}).get("tools")
    if tools is None:
        state["prefs"] = Prefs()
        state["prefs_update_error"] = {"detail": "tools_not_initialized"}
        return state

    # Read current prefs
    try:
        prefs_raw = await tools.call("agent.get_prefs", {})
        prefs = _normalize_prefs(prefs_raw)
    except MCPError as e:
        state["prefs"] = Prefs()
        state["prefs_update_error"] = {"detail": f"get_prefs failed: {e}"}
        return state
    

    # Update prefs from slots
    slots = state.get("slots", {}) or {}
    update_info = _extract_prefs(slots)
    if update_info:
        try:
            updated_raw = await tools.call("agent.update_prefs", {
                "updated_info_json": json.dumps(update_info)
            })
            prefs = _normalize_prefs(updated_raw) or prefs
        except MCPError as e:
            state["prefs_update_error"] = {"detail": f"update_prefs failed: {e}"}
    

    # Save new prefs into state['prefs]
    state["prefs"] = prefs
    
    return state
