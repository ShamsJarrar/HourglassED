from sqlalchemy.orm import Session
from models.event_class import EventClass
from models.user import User
from dependencies import get_current_user, get_db


def normalize_string(txt: str) -> str:
    return txt.strip().lower()


def get_event_class(
        event_class_name: str,
        db: Session,
        user: User
) -> EventClass:

    event_class_name = normalize_string(event_class_name)

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
    
    return event_class