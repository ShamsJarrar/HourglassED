from .schemas import (
    ProposeCreateRequest, ProposeUpdateRequest, ProposeDeleteRequest, AgentUserPrefsUpdate
)
from pydantic import ValidationError
from .http import request_json
from .config import DEFAULT_LIST_WINDOW_DAYS
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
import json


def _iso(date: datetime) -> str:
    return date.isoformat()


def register_tools(mcp):
    @mcp.tool("agent.get_prefs")
    async def get_prefs() -> Any:
        return await request_json("GET", "/agent/prefs")

                
    @mcp.tool("agent.update_prefs")
    async def update_prefs(updated_info_json: str) -> Any:
        try:
            body = AgentUserPrefsUpdate.model_validate_json(updated_info_json).model_dump(exclude_none=True)
        except ValidationError as e:
            return {"error": "invalid_update_prefs", "detail": e.errors()}
        
        return await request_json("PUT", "/agent/prefs", json=body)


    @mcp.tool("agent.list_events")
    async def list_events(
        start_time: Optional[str] = None, 
        end_time: Optional[str] = None, 
        title: Optional[str] = None,
        owned_only: Optional[bool] = False,
        event_types_json: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Any:

        now = datetime.now(timezone.utc)
        start = datetime.fromisoformat(start_time) if start_time else now
        end = datetime.fromisoformat(end_time) if end_time else (now + timedelta(days=DEFAULT_LIST_WINDOW_DAYS))

        params: dict[str, Any] = {
            "start_time": _iso(start),      # converting to isoformat to match the frontend format when sending to the backend
            "end_time": _iso(end),
            "owned_only": str(owned_only).lower(),
            "limit": limit,
            "offset": offset
        }

        if title: params["title"] = title
        if event_types_json:
            try:
                types = json.loads(event_types_json)
                if isinstance(types, list) and all(isinstance(x, int) for x in types):
                    for t in types: 
                        params.setdefault("event_types[]", []).append(str(t))
            except json.JSONDecodeError:
                pass
        
        return await request_json("GET", "/agent/events", params=params)


    @mcp.tool("agent.get_availability")
    async def get_availability(
        start_time: str,
        end_time: str,
        min_block_minutes: int = 60,
    ) -> Any:

        return await request_json("GET", "/agent/availability", params={
            "start_time": start_time, "end_time": end_time, "min_block_minutes": min_block_minutes
        })


    @mcp.tool("agent.propose_create_event")
    async def propose_create_event(draft_json: str) -> Any:
        try:
            body = ProposeCreateRequest.model_validate_json(draft_json).model_dump()
        except ValidationError as e:
            return {"error": "invalid_propose_create_event", "detail": e.errors()}
        
        draft = body["draft"]
        draft["start_time"] = _iso(datetime.fromisoformat(draft["start_time"]))
        draft["end_time"] = _iso(datetime.fromisoformat(draft["end_time"]))

        return await request_json("POST", "/agent/propose/create_event", json=body)


    @mcp.tool("agent.propose_update_event")
    async def propose_update_event(draft_json: str) -> Any:
        try:
            body = ProposeUpdateRequest.model_validate_json(draft_json).model_dump()
        except ValidationError as e:
            return {"error": "invalid_propose_update_event", "detail": e.errors()}

        draft = body["draft"]
        for key in ("start_time", "end_time", "recurrence_end"):
            if draft.get(key):
                draft[key] = _iso(datetime.fromisoformat(draft[key]))
        
        return await request_json("POST", "/agent/propose/update_event", json=body)


    @mcp.tool("agent.propose_delete_event")
    async def propose_delete_event(draft_json: str) -> Any:
        try:
            body = ProposeDeleteRequest.model_validate_json(draft_json).model_dump()
        except ValidationError as e:
            return {"error": "invalid_propose_delete_event", "detail": e.errors()}
        
        return await request_json("POST", "/agent/propose/delete_event", json=body)


    @mcp.tool("agent.list_proposals")
    async def list_proposals(
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Any:

        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        
        return await request_json("GET", "/agent/proposals", params=params)


    @mcp.tool("agent.get_proposal")
    async def get_proposal(proposal_id: int) -> Any:
        return await request_json("GET", f"/agent/proposals/{proposal_id}")


    @mcp.tool("agent.approve_proposal")
    async def approve_proposal(proposal_id: int) -> Any:
        return await request_json("POST", f"/agent/proposals/{proposal_id}/approve")


    @mcp.tool("agent.reject_proposal")
    async def reject_proposal(proposal_id: int) -> Any:
        return await request_json("POST", f"/agent/proposals/{proposal_id}/reject")