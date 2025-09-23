from datetime import datetime, timedelta
from typing import Optional, Any
from sqlalchemy.orm import Session
from models.event import Event
from models.agent_audit_log import AgentAuditLog
from utils.time import now_utc_naive


DEFAULT_TTL_HOURS = 72


def expiry_time(hours: int = DEFAULT_TTL_HOURS) -> datetime:
    return now_utc_naive() + timedelta(hours=hours)


def audit(
    db: Session,
    user_id: int,
    event: str,
    proposal_id: Optional[int] = None,
    payload_json: Optional[dict[str, Any]] = None
) -> None:

    """audit log entry"""
    aud = AgentAuditLog(
        user_id=user_id,
        event=event,
        proposal_id=proposal_id,
        payload_json=payload_json or {}
    )
    db.add(aud)
    db.commit()
    db.refresh(aud)


def build_diff_create(draft: dict[str, Any]) -> dict[str, list[Any]]:
    """
    build a diff create payload for an agent proposal
    {
    "title":        [null, "New title"],       // create: no old value
    "start_time":   [null, "2025-09-17T18:00Z"],
    "end_time":     [null, "2025-09-17T20:00Z"]
    }
    """

    diff: dict[str, list[Any]] = {}
    for key, value in draft.items():
        diff[key] = [None, value]
    return diff


def build_diff_update(ev: Event, updates_draft: dict[str, Any]) -> dict[str, list[Any]]:
    """
    build a diff update payload for an agent proposal
    before: from event
    after: from updates_draft

    {
    "title":        ["Old title", "New title"],       // update: has old value
    "start_time":   ["2025-09-17T18:00Z", "2025-09-17T19:00Z"],
    "end_time":     ["2025-09-17T20:00Z", "2025-09-17T21:00Z"]
    }
    """

    field_map = {
        "event_type": "event_type",
        "title": "title",
        "header": "header",
        "notes": "notes",
        "color": "color",
        "timezone": "timezone",
        "start_time": "start_time",
        "end_time": "end_time",
        "series_id": "series_id",
        "is_exception": "is_exception",
        "update_scope": None,
        "delete_scope": None
    }

    diff: dict[str, list[Any]] = {}
    for req_key, ev_attr in field_map.items():
        if req_key not in updates_draft:
            continue

        before_val = getattr(ev, ev_attr, None)
        if isinstance(before_val, datetime):
            before_val = before_val.isoformat()
        
        new_val = updates_draft[req_key]
        if isinstance(new_val, datetime):
            new_val = new_val.isoformat()
        
        diff[req_key] = [before_val, new_val]
    
    return diff
