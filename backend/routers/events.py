from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_current_user, get_db
from utils.helpers import normalize_string
from models.user import User
from models.event_class import EventClass
from models.event import Event
from models.event_invitation import EventInvitation
from schemas.event import EventCreate, EventResponse, EventUpdate
from typing import List


router = APIRouter(prefix='/event', tags=['Event'])


@router.post('/', response_model=EventResponse)
def create_event(
    event_info: EventCreate, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    event_class_name = normalize_string(event_info.event_type)

    # check if event class is builtin
    event_class = db.query(EventClass).filter(
        EventClass.class_name == event_class_name,
        EventClass.is_builtin == True
    ).first()

    # if not built in, then check if custom class
    # is already added by the user or not
    if not event_class:
        event_class = db.query(EventClass).filter(
            EventClass.class_name == event_class_name,
            EventClass.created_by == user.user_id
        ).first()
    

    # if event_class still not found, add it to db
    if not event_class:
        event_class = EventClass(
            class_name = event_class_name,
            created_by = user.user_id,
            is_builtin = False
        )
        db.add(event_class)
        db.commit()
        db.refresh(event_class)


    if event_info.start_time >= event_info.end_time:
        raise HTTPException(status_code=400, 
                            detail="start_time must be before end_time")

    
    new_event = Event(
        event_type = event_class.class_id,
        header = event_info.header,
        title = event_info.title,
        start_time = event_info.start_time,
        end_time = event_info.end_time,
        recurrence_pattern = event_info.recurrence_pattern,
        color = event_info.color,
        notes = event_info.notes,
        linked_event_id = event_info.linked_event_id,
        user_id = user.user_id
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event


@router.get('/', response_model=List[EventResponse])
def get_all_events(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    user_events = db.query(Event).filter(
        Event.user_id == user.user_id
    ).all()

    
    # TODO: query shared events with user from event invitations
    # TODO: drop shared events table due to redudancy
    # TODO: add querying filters like (event_type, date range), etc

    return user_events


