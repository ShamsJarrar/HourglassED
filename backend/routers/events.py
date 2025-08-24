from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from dependencies import get_current_user, get_db
from utils.helpers import get_event_class
from models.user import User
from models.event import Event
from models.event_invitation import EventInvitation, EventInvitationStatus
from models.event_class import EventClass
from models.friend import Friend
from schemas.event import EventCreate, EventResponse, EventUpdate
from schemas.event_class import EventClassResponse
from typing import List, Optional
from datetime import datetime
from logger import logger


router = APIRouter(prefix='/event', tags=['Event'])


@router.post('/', response_model=EventResponse)
def create_event(
    event_info: EventCreate, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    event_class = get_event_class(event_info.event_type, db, user)

    if event_info.start_time >= event_info.end_time:
        logger.warning(f"User {user.user_id} added invalid start and end times when creating an event")
        raise HTTPException(status_code=400, 
                            detail="start_time must be before end_time")
    
    new_event = Event(
        event_type = event_class.class_id,
        header = event_info.header,
        title = event_info.title,
        start_time = event_info.start_time,
        end_time = event_info.end_time,
        recurring_event_id = event_info.recurring_event_id,
        color = event_info.color,
        notes = event_info.notes,
        linked_event_id = event_info.linked_event_id,
        user_id = user.user_id
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    logger.info(f"User {user.user_id} created event '{new_event.title}' with id {new_event.event_id}")
    return new_event



@router.get('/', response_model=List[EventResponse])
def get_user_events(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    event_types: Optional[List[int]] = Query(None),
    event_types_alt: Optional[List[int]] = Query(None, alias='event_types[]'),
    owned_only: Optional[bool] = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    filters = []

    # Proper overlap filtering when both bounds are provided:
    # (event.start < viewEnd) AND (event.end > viewStart)
    if start_time is not None and end_time is not None:
        filters.append(Event.start_time < end_time)
        filters.append(Event.end_time > start_time)
    else:
        if start_time is not None:
            filters.append(Event.end_time > start_time)
        if end_time is not None:
            filters.append(Event.start_time < end_time)
    # Filter by any of the selected event types if provided (support 'event_types' and 'event_types[]')
    selected_types = event_types or event_types_alt
    if selected_types:
        filters.append(Event.event_type.in_(selected_types))

    user_events = db.query(Event).filter(
        Event.user_id == user.user_id,
        *filters
    ).all()

    shared_event_ids = db.query(EventInvitation.event_id).filter(
        EventInvitation.invited_user_id == user.user_id,
        EventInvitation.status == EventInvitationStatus.accepted
    ).subquery()

    shared_events = db.query(Event).filter(
        Event.event_id.in_(shared_event_ids),
        *filters
    ).all()
    
    logger.debug(f"User {user.user_id} fetched their events. owned_only={owned_only}, filters={filters}")

    if owned_only:
        return user_events
    return user_events + shared_events



@router.get('/classes', response_model=List[EventClassResponse])
def list_event_classes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    builtin = db.query(EventClass).filter(EventClass.is_builtin == True).all()
    custom = db.query(EventClass).filter(EventClass.created_by == user.user_id).all()
    return builtin + custom



@router.get('/{event_id}', response_model=EventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    event = db.query(Event).filter(
        Event.event_id == event_id
    ).first()

    if not event:
        logger.warning(f"User {user.user_id} tried to access a non-existent event")
        raise HTTPException(status_code=404, detail="Event does not exist")
    
    if event.user_id == user.user_id:
        logger.debug(f"User {user.user_id} fetched event with id:{event_id}")
        return event
    

    is_shared_event = db.query(EventInvitation).filter(
        EventInvitation.event_id == event_id,
        EventInvitation.invited_user_id == user.user_id,
        EventInvitation.status == EventInvitationStatus.accepted
    ).first()

    if not is_shared_event:
        logger.warning(f"User {user.user_id} is not authorized to access event {event_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to access this event")
    

    logger.debug(f"User {user.user_id} fetched event with id:{event.event_id}")
    return event



@router.put('/{event_id}', response_model=EventResponse)
def update_event(
    event_id: int,
    updated_info: EventUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    event = db.query(Event).filter(Event.event_id == event_id).first()

    if not event:
        logger.warning(f"User {user.user_id} tried to access a non-existent event")
        raise HTTPException(status_code=404, detail="Event does not exist")
    
    if event.user_id != user.user_id:
        logger.warning(f"User {user.user_id} is not authorized to edit event {event.event_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to edit this event")
    
    if updated_info.event_type is not None:
        event_class = get_event_class(updated_info.event_type, db, user)
        event.event_type = event_class.class_id
    
    for field in ["header", "title", "start_time", "end_time", "color", "notes", "linked_event_id", "recurring_event_id"]:
        value = getattr(updated_info, field)
        if value is not None:
            setattr(event, field, value)


    db.commit()
    db.refresh(event)
    logger.info(f"User {user.user_id} updated event {event_id}")
    return event



@router.delete('/{event_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    event = db.query(Event).filter(Event.event_id == event_id).first()

    if not event:
        logger.warning(f"User {user.user_id} tried to access a non-existent event")
        raise HTTPException(status_code=404, detail="Event does not exist")
    
    if event.user_id != user.user_id:
        logger.warning(f"User {user.user_id} is not authorized to delete event {event.event_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to delete this event")
    

    invitations_to_event = db.query(EventInvitation).filter(
        EventInvitation.event_id == event_id,
        EventInvitation.status.in_([
            EventInvitationStatus.pending,
            EventInvitationStatus.accepted
        ])
    ).all()

    
    db.delete(event)
    db.commit()
    logger.info(f"User {user.user_id} deleted event {event_id}. {len(invitations_to_event)} invitations marked as deleted.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# frontend calls get all sent invites to get invited_user_id
@router.delete('/{event_id}/remove/{invited_user_id}', status_code=status.HTTP_204_NO_CONTENT)
def remove_user_from_event(
    event_id: int,
    invited_user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    event = db.query(Event).filter(
        Event.event_id == event_id
    ).first()

    if not event:
        logger.warning(f"User {user.user_id} tried to access a non-existent event")
        raise HTTPException(status_code=404, detail="Event does not exist")
    
    if event.user_id != user.user_id:
        logger.warning(f"User {user.user_id} is not authorized to access event {event.event_id}")
        raise HTTPException(status_code=403, detail="You are not allowed to access this event")
    

    invite = db.query(EventInvitation).filter(
        EventInvitation.event_id == event_id,
        EventInvitation.invited_user_id == invited_user_id,
        EventInvitation.status == EventInvitationStatus.accepted
    ).first()

    if not invite:
        logger.warning(f"User {user.user_id} tried to remove {invited_user_id} but didn't share event or invitee didn't accept it")
        raise HTTPException(status_code=404, detail="Event not shared with user or user did not accept invite")
    

    invite.status = EventInvitationStatus.removed
    db.commit()
    logger.info(f"User {user.user_id} removed user {invited_user_id} from event {event_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@router.delete('/{event_id}/withdraw', status_code=status.HTTP_204_NO_CONTENT)
def withdraw_from_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    invite = db.query(EventInvitation).filter(
        EventInvitation.event_id == event_id,
        EventInvitation.invited_user_id == user.user_id,
        EventInvitation.status == EventInvitationStatus.accepted
    ).first()

    if not invite:
        logger.warning(f"User {user.user_id} does not have an accepted invitation to event {event_id}")
        raise HTTPException(status_code=404, detail="You do not have an accepted invitation for this event")


    invite.status = EventInvitationStatus.withdrawn
    db.commit()
    logger.info(f"User {user.user_id} withdrew from event {event_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


 
