"""
Tools node:
- Read calendar context from the backend via MCP tools.
- Store results in state.calendar = {events: ..., availability: ...}.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timedelta, timezone
from ..state import AgentState
from ..mcp_tools import MCPTools, MCPError
from ..config import DEFAULT_LIST_WINDOWS




def time_window_from_slots(state: AgentState) -> tuple[str, str]:
    """
    Helper to decide [start, end] time window to query.
    - if slots specify start_time and end_time, use them.
    - Else, [now, now + DEFAULT_LIST_WINDOWS]
    Always return ISO-8601 strings.
    """

    slots = state.get("slots", {}) or {}
    now = datetime.now(timezone.utc)
    start = slots.get("start_time") or now.isoformat()
    end = slots.get("end_time") or (now + timedelta(days=DEFAULT_LIST_WINDOWS)).isoformat()
    return str(start), str(end)


async def read_calendar(state: AgentState, config: Optional[Dict[str, Any]] | None = None) -> AgentState:
    """
    GET:
        - agent.list_events       (bounded by timw window)
        - agent.get_availability  (bounded by time window and min_block_minutes if provided)
    Results saved in state.calendar = {events: ..., availability: ...}.

    Any transport error is replaced with a placeholder so that
    downstream nodes don't fail.
    """
    tools: MCPTools = (config or {}).get("tools")
    if tools is None:
        state["calendar"] = {"error": "tools_not_initialized"}
        return state

    start, end = time_window_from_slots(state)
    min_block_minutes = int(state.get("slots", {}).get("min_block_minutes") or 60)

    # agent.list_events
    try:
        events = await tools.call("agent.list_events", {
            "start_time": start,
            "end_time": end,
            "limit": 200,
            "offset": 0
        })
    except Exception as e:
        events = {"error": "mcp_list_events_failed", "detail": str(e)}
    

    # agent.get_availability
    try:
        availability = await tools.call("agent.get_availability", {
            "start_time": start,
            "end_time": end,
            "min_block_minutes": min_block_minutes
        })
    except Exception as e:
        availability = {"error": "mcp_get_availability_failed", "detail": str(e)}
    

    state["calendar"] = {"events": events, "availability": availability}
    return state
