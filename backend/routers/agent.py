from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from dependencies import get_db, get_current_user
from utils.time import to_naive_utc, now_utc_naive
from utils.agent import expiry_time, audit, build_diff_create, build_diff_update
from utils.helpers import get_event_class
from utils.recurrence import create_series_and_seed, reapply_series_from
from models.user import User
from models.event import Event
from models.event_invitation import EventInvitation, EventInvitationStatus
from models.agent_proposal import AgentProposal, AgentProposalStatus, AgentProposalType
from models.agent_user_prefs import AgentUserPrefs
from models.recurrence_series import RecurrenceSeries
from schemas.event import EventResponse
from schemas.agent import AgentUserPrefsResponse, AgentUserPrefsUpdate, AgentProposalResponse, ProposeCreateRequest, ProposeUpdateRequest, ProposeDeleteRequest
from datetime import datetime
from typing import Optional, Any, List
from logger import logger



router = APIRouter(prefix='/agent', tags=['Agent'])



### Agent User Preferences (Agent Memory)
@router.get('/prefs', response_model=AgentUserPrefsResponse)
def get_prefs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    prefs = db.query(AgentUserPrefs).filter(AgentUserPrefs.user_id == user.user_id).first()

    if not prefs:
        prefs = AgentUserPrefs(user_id=user.user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.put('/prefs', response_model=AgentUserPrefsResponse)
def update_prefs(
    updated_info: AgentUserPrefsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    prefs = db.query(AgentUserPrefs).filter(AgentUserPrefs.user_id == user.user_id).first()
    if not prefs:
        prefs = AgentUserPrefs(user_id=user.user_id)
        db.add(prefs)
        db.flush()
    
    for field, value in updated_info.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    
    db.commit()
    db.refresh(prefs)
    audit(db, user.user_id, "update_prefs", payload_json=updated_info.model_dump(exclude_unset=True))
    return prefs



### Calendar read
@router.get('/events', response_model=List[EventResponse])
def get_events(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    event_types: Optional[List[int]] = Query(None),
    event_types_alt: Optional[List[int]] = Query(None, alias='event_types[]'),
    owned_only: Optional[bool] = Query(False),
    title: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    filters = []

    if start_time is not None and end_time is not None:
        filters.append(Event.start_time < end_time)
        filters.append(Event.end_time > start_time)
    else:
        if start_time is not None:
            filters.append(Event.end_time > start_time)
        if end_time is not None:
            filters.append(Event.start_time < end_time)
    
    selected_types = event_types or event_types_alt
    if selected_types:
        filters.append(Event.event_type.in_(selected_types))
    
    if title:
        filters.append(Event.title.ilike(f"%{title}%"))
    

    shared_event_ids = db.query(EventInvitation.event_id).filter(
        EventInvitation.invited_user_id == user.user_id,
        EventInvitation.status == EventInvitationStatus.accepted
    )

    if owned_only:
        select = (Event.user_id == user.user_id)
    else:
        select = or_(
            Event.user_id == user.user_id,
            Event.event_id.in_(shared_event_ids)
        )
    
    events = db.query(Event).filter(select, *filters).order_by(Event.start_time.asc()).offset(offset).limit(limit).all()
    return events



@router.get('/availability')
def get_availability(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    min_block_minutes: int = Query(60, ge=15, le=360),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    if start_time >= end_time:
        logger.warning(f"User {user.user_id} tried to get availability with invalid start and end times")
        raise HTTPException(status_code=400, detail="start_time must be before end_time")
    
    events = db.query(Event).filter(
        Event.user_id == user.user_id,
        Event.start_time < end_time,
        Event.end_time > start_time
    ).order_by(Event.start_time.asc()).all()


    busy =  [{"start": e.start_time, "end": e.end_time, "title": e.title, "event_id": e.event_id} for e in events]
    
    merged: List[dict[str, Any]] = []
    for b in busy:
        if not merged:
            merged.append(dict(b))
            continue
        
        last = merged[-1]
        if b["start"] <= last["end"]:
            if b["end"] > last["end"]:
                last["end"] = b["end"]
        else:
            merged.append(dict(b))
    
    free: List[dict[str, datetime]] = []
    cursor = start_time
    for m in merged:
        if m["start"] > cursor:
            dur = (m["start"] - cursor).total_seconds() / 60
            if dur >= min_block_minutes:
                free.append({"start": cursor, "end": m["start"]})
        cursor = max(cursor, m["end"])
    
    if cursor < end_time:
        dur = (end_time - cursor).total_seconds() / 60
        if dur >= min_block_minutes:
            free.append({"start": cursor, "end": end_time})


    prefs =  db.query(AgentUserPrefs).filter(AgentUserPrefs.user_id == user.user_id).first()
    tz = prefs.timezone if (prefs and prefs.timezone) else "UTC"
    
    return {"timezone": tz, "busy": busy, "free": free}



### Agent Proposal
@router.post('/propose/create_event', response_model=AgentProposalResponse)
def propose_create_event(
    req: ProposeCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    event_draft = req.draft

    if event_draft.start_time >= event_draft.end_time:
        logger.warning(f"User {user.user_id} tried to create event with invalid start and end times")
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    # cannot provide both series_id and recurrence_pattern, can add to existing series or create a new series
    if event_draft.series_id is not None and event_draft.recurrence_pattern is not None:
        raise HTTPException(
            status_code=400,
            detail="Provide either series_id or recurrence_pattern, not both"
        )
    
    payload_json = {
        "action": "create_event",
        "draft": {
            "event_type": event_draft.event_type,                # given as string, but when commited to db, it will be normalized to int
            "title": event_draft.title,
            "start_time": to_naive_utc(event_draft.start_time),
            "end_time": to_naive_utc(event_draft.end_time),
            "timezone": event_draft.timezone,
            "header": event_draft.header,
            "color": event_draft.color,
            "notes": event_draft.notes,
            "series_id": event_draft.series_id,
            "recurrence_pattern": event_draft.recurrence_pattern,
        }
    }

    diff_json = build_diff_create({
        "event_type": event_draft.event_type,
        "title": event_draft.title,
        "start_time": event_draft.start_time,
        "end_time": event_draft.end_time,
        "timezone": event_draft.timezone,
        "header": event_draft.header,
        "color": event_draft.color,
        "notes": event_draft.notes,
        "series_id": event_draft.series_id,
    })

    proposal = AgentProposal(
        user_id=user.user_id,
        proposal_type=AgentProposalType.create_event,
        target_event_id=None,
        payload_json=payload_json,
        diff_json=diff_json,
        reasoning_summary=req.reasoning_summary[:255],
        status=AgentProposalStatus.pending,
        expires_at=expiry_time()
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    audit(db, user.user_id, "propose_create_event", proposal_id=proposal.proposal_id, payload_json=payload_json)
    return proposal



@router.post('/propose/update_event', response_model=AgentProposalResponse)
def propose_update_event(
    req: ProposeUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    event_draft = req.draft
    event = db.query(Event).filter(
        Event.event_id == event_draft.event_id,
        Event.user_id == user.user_id
    ).first()

    if not event:
        logger.warning(f"User {user.user_id} tried to update a non-existent event")
        raise HTTPException(status_code=404, detail="Event does not exist")
    

    series_id = event_draft.series_id or event.series_id
    if event_draft.update_scope == "series" and not series_id:
        logger.warning(f"Agent tried to update event series but no series id was provided")
        raise HTTPException(status_code=400, detail="series_id required for update_scope='series'")

    
    updates: dict[str, Any] = {}
    for field in ["event_type", "header", "title", "color", "notes", "timezone"]:
        value = getattr(event_draft, field)
        if value is not None:
            updates[field] = value

    if event_draft.start_time is not None:
        updates["start_time"] = to_naive_utc(event_draft.start_time)

    if event_draft.end_time is not None:
        updates["end_time"] = to_naive_utc(event_draft.end_time)
    
    if "start_time" in updates and "end_time" in updates and updates["end_time"] <= updates["start_time"]:
        logger.warning(f"Agent tried to update event {event.event_id} with invalid start and end times")
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    if event_draft.update_scope == "series":
        series_updates: dict[str, Any] = {}
        if event_draft.recurrence_pattern is not None:
            series_updates["recurrence_pattern"] = event_draft.recurrence_pattern
        if event_draft.recurrence_end is not None:
            series_updates["recurrence_end"] = to_naive_utc(event_draft.recurrence_end)
        
        if series_updates:
            updates["series"] = series_updates

    payload = {
        "action": "update_event",
        "event_id": event.event_id,
        "updates": updates,
        "update_scope": event_draft.update_scope,
        "series_id": series_id,
    }

    updates_draft = event_draft.model_dump(exclude_unset=True)
    updates_draft["series_id"] = series_id
    updates_draft["update_scope"] = event_draft.update_scope
    diff_json = build_diff_update(event, updates_draft)

    proposal = AgentProposal(
        user_id=user.user_id,
        proposal_type=AgentProposalType.update_event,
        target_event_id=event.event_id,
        payload_json=payload,
        diff_json=diff_json,
        reasoning_summary=req.reasoning_summary[:255],
        status=AgentProposalStatus.pending,
        expires_at=expiry_time()
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    audit(db, user.user_id, "propose_update_event", proposal_id=proposal.proposal_id, payload_json=payload)
    return proposal



@router.post('/propose/delete_event', response_model=AgentProposalResponse)
def propose_delete_event(
    req: ProposeDeleteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    event_draft = req.draft
    event = db.query(Event).filter(
        Event.event_id == event_draft.event_id,
        Event.user_id == user.user_id
    ).first()

    if not event:
        logger.warning(f"User {user.user_id} tried to delete a non-existent event")
        raise HTTPException(status_code=404, detail="Event does not exist")
    

    series_id = event_draft.series_id or event.series_id
    if event_draft.delete_scope == "series" and not series_id:
        logger.warning(f"Agent tried to delete event series but no series id was provided")
        raise HTTPException(status_code=400, detail="series_id required for delete_scope='series'")
    

    payload = {
        "action": "delete_event",
        "event_id": event.event_id,
        "delete_scope": event_draft.delete_scope,
        "series_id": series_id,
    }

    diff_json = {
        "delete_scope": [None, event_draft.delete_scope],
        "series_id": [event.series_id, series_id],
        "deleted_event_id": [event.event_id, None] if event_draft.delete_scope == "occurrence" else [None, None]
    }

    proposal = AgentProposal(
        user_id=user.user_id,
        proposal_type=AgentProposalType.delete_event,
        target_event_id=event.event_id,
        payload_json=payload,
        diff_json=diff_json,
        reasoning_summary=req.reasoning_summary[:255],
        status=AgentProposalStatus.pending,
        expires_at=expiry_time()
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    audit(db, user.user_id, "propose_delete_event", proposal_id=proposal.proposal_id, payload_json=payload)
    return proposal



### Proposals
@router.get('/proposals')
def list_proposals(
    status: Optional[AgentProposalStatus] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    proposals = db.query(AgentProposal).filter(AgentProposal.user_id == user.user_id)
    if status:
        proposals = proposals.filter(AgentProposal.status == status)
    
    proposals = proposals.order_by(AgentProposal.created_at.desc()).offset(offset).limit(limit).all()
    return {"proposals": proposals}



@router.get('/proposals/{proposal_id}', response_model=AgentProposalResponse)
def get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    proposal = db.query(AgentProposal).filter(
        AgentProposal.proposal_id == proposal_id, 
        AgentProposal.user_id == user.user_id
    ).first()

    if not proposal:
        logger.warning(f"User {user.user_id} tried to get a non-existent proposal")
        raise HTTPException(status_code=404, detail="Proposal does not exist")
    
    return proposal



### Human Gate (frontend only endpoints for proposal commits)
@router.post('/proposals/{proposal_id}/approve', status_code=status.HTTP_204_NO_CONTENT)
def approve_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    proposal = db.query(AgentProposal).filter(
        AgentProposal.proposal_id == proposal_id,
        AgentProposal.user_id == user.user_id
    ).first()

    if not proposal or proposal.status != AgentProposalStatus.pending:
        logger.warning(f"User {user.user_id} tried to approve a non-existent/non-pending proposal")
        raise HTTPException(status_code=404, detail="Proposal does not exist or is not pending")
    
    if proposal.expires_at < now_utc_naive():
        proposal.status = AgentProposalStatus.expired
        db.commit()
        logger.warning(f"User {user.user_id} tried to approve an expired proposal")
        raise HTTPException(status_code=400, detail="Proposal has expired")
    

    payload_json = proposal.payload_json or {}
    action = payload_json.get("action")

    try:


        if action == "create_event":
            draft = payload_json.get("draft") or {}

            recurrence_pattern = draft.get("recurrence_pattern")
            series_id = draft.get("series_id")
            recurrence_end = draft.get("recurrence_end")

            event_class = get_event_class(draft.get("event_type"), db, user)

            if recurrence_pattern and series_id is None:
                series = create_series_and_seed(
                    db=db,
                    user_id=user.user_id,
                    event_type=event_class.class_id,
                    title=draft["title"],
                    header=draft.get("header"),
                    start_time=draft["start_time"],      # already naive UTC from proposal
                    end_time=draft["end_time"],          # already naive UTC
                    timezone_name=draft.get("timezone") or "UTC",
                    recurrence_pattern=recurrence_pattern,
                    recurrence_end=recurrence_end,             
                    color=draft.get("color"),
                    notes=draft.get("notes"),
                )
                if not series:
                    logger.error(f"Failed to create series for proposal {proposal_id}")
                    raise HTTPException(status_code=400, detail="Failed to create series")
            
            else:
                if draft["start_time"] >= draft["end_time"]:
                    logger.error(f"User {user.user_id} tried to create event with invalid start and end times")
                    raise HTTPException(status_code=400, detail="start_time must be before end_time")
                
                event = Event(
                    event_type=event_class.class_id,
                    title=draft["title"],
                    header=draft.get("header"),
                    start_time=draft["start_time"],
                    end_time=draft["end_time"],
                    color=draft.get("color"),
                    notes=draft.get("notes"),
                    user_id=user.user_id,
                    series_id=series_id,
                    is_exception=False,
                    timezone=draft.get("timezone") or "UTC",
                )
                db.add(event)
                db.flush()
        

        elif action == "update_event":
            event_id = payload_json['event_id']
            updates = dict(payload_json.get('updates') or {})
            scope = payload_json.get('update_scope', 'occurrence')
            series_id = payload_json.get('series_id')

            if "event_type" in updates and isinstance(updates["event_type"], str):
                updates["event_type"] = get_event_class(updates["event_type"], db, user).class_id
            
            if scope == "occurrence":
                event = db.query(Event).filter(
                    Event.event_id == event_id,
                    Event.user_id == user.user_id
                ).first()

                if not event:
                    logger.error(f"User {user.user_id} tried to update a non-existent event")
                    raise HTTPException(status_code=404, detail="Event does not exist")
                
                new_start = updates.get("start_time", event.start_time)
                new_end   = updates.get("end_time", event.end_time)
                if new_start and new_end and new_start >= new_end:
                    logger.error(f"User {user.user_id} tried to update an event with invalid start and end times")
                    raise HTTPException(status_code=400, detail="start_time must be before end_time")
                
                changed = False
                if "event_type" in updates and event.event_type != updates["event_type"]:
                    event.event_type = updates["event_type"]
                    changed = True

                if "start_time" in updates and event.start_time != updates["start_time"]:
                    event.start_time = to_naive_utc(updates["start_time"])
                    changed = True

                if "end_time" in updates and event.end_time != updates["end_time"]:
                    event.end_time = to_naive_utc(updates["end_time"])
                    changed = True

                for k in ["header", "title", "color", "notes"]:
                    if k in updates and getattr(event, k) != updates[k]:
                        setattr(event, k, updates[k])
                        changed = True

                if changed:
                    db.flush()
            
            elif scope == "series":
                if not series_id:
                    logger.error(f"Agent tried to update event series but no series id was provided")
                    raise HTTPException(status_code=400, detail="series_id required for update_scope='series'")
                
                series_updates = updates.get("series") or {}
                if series_updates:
                    new_rrule = series_updates.get("recurrence_pattern")
                    new_end = series_updates.get("recurrence_end")
                    pivot = payload_json.get("pivot") or now_utc_naive()
                    months = int(payload_json.get("months") or 6)

                    updated_series = reapply_series_from(
                        db=db,
                        series_id=series_id,
                        pivot=pivot,
                        new_rrule=new_rrule,
                        new_recurrence_end=new_end,
                        window_months=months
                    )

                    if not updated_series:
                        logger.error(f"Agent tried to update series but series not found")
                        raise HTTPException(status_code=400, detail="Series does not exist")
                
                event_updates = {}
                for k in ["event_type", "header", "title", "color", "notes", "start_time", "end_time"]:
                    if k in updates:
                        if k in ("start_time", "end_time"):
                            event_updates[k] = to_naive_utc(updates[k])
                        else:
                            event_updates[k] = updates[k]

                if event_updates:
                    if ("start_time" in event_updates and "end_time" in event_updates and
                        event_updates["end_time"] <= event_updates["start_time"]):
                        logger.error(f"Agent tried to update event series with invalid start and end times")
                        raise HTTPException(status_code=400, detail="end_time must be after start_time")

                    changed = db.query(Event).filter(
                        Event.user_id == user.user_id,
                        Event.series_id == series_id,
                        Event.is_exception == False
                    ).update(event_updates, synchronize_session="fetch")
            else:
                raise HTTPException(status_code=400, detail="Invalid update_scope")
        

        elif action == "delete_event":
            event_id = payload_json["event_id"]
            scope = payload_json.get("delete_scope", "occurrence")
            series_id = payload_json.get("series_id")

            if scope == "occurrence":
                event = db.query(Event).filter(
                    Event.event_id == event_id,
                    Event.user_id == user.user_id
                ).first()

                if not event:
                    logger.error(f"Agent tried to delete a non-existent event")
                    raise HTTPException(status_code=404, detail="Event does not exist")
                
                db.delete(event)
                db.flush()

            elif scope == "series":
                if not series_id:
                    logger.error(f"Agent tried to delete event series but no series id was provided")
                    raise HTTPException(status_code=400, detail="series_id required for delete_scope='series'")
                
                series = db.query(RecurrenceSeries).filter(
                    RecurrenceSeries.series_id == series_id,
                    RecurrenceSeries.user_id == user.user_id
                ).first()

                if not series:
                    logger.error(f"Agent tried to delete a non-existent series")
                    raise HTTPException(status_code=400, detail="Series does not exist")
                
                db.delete(series)
                db.flush()
            else:
                raise HTTPException(status_code=400, detail="Invalid delete_scope")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        proposal.status = AgentProposalStatus.committed
        db.commit()
        audit(db, user.user_id, "approve_proposal", proposal_id=proposal.proposal_id, payload_json=proposal.payload_json)
        return
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving proposal {proposal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve proposal")
        
       


@router.post('/proposals/{proposal_id}/reject', status_code=status.HTTP_204_NO_CONTENT)
def reject_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    proposal = db.query(AgentProposal).filter(
        AgentProposal.proposal_id == proposal_id,
        AgentProposal.user_id == user.user_id
    ).first()

    if not proposal or proposal.status != AgentProposalStatus.pending:
        logger.warning(f"User {user.user_id} tried to reject a non-existent/non-pending proposal")
        raise HTTPException(status_code=404, detail="Proposal does not exist or is not pending")
    
    if proposal.expires_at < now_utc_naive():
        proposal.status = AgentProposalStatus.expired
        db.commit()
        logger.warning(f"User {user.user_id} tried to reject an expired proposal")
        raise HTTPException(status_code=400, detail="Proposal has expired")
    
    proposal.status = AgentProposalStatus.rejected
    db.commit()
    audit(db, user.user_id, "reject_proposal", proposal_id=proposal.proposal_id, payload_json=proposal.payload_json)
    return
    