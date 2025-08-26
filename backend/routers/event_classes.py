from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from models.user import User
from models.event_class import EventClass
from schemas.event_class import EventClassResponse
from typing import List, Optional
from dependencies import get_current_user, get_db
from logger import logger

router = APIRouter(prefix='/classes', tags=['Event Classes'])


@router.get('/', response_model=List[EventClassResponse])
def list_event_classes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    builtin = db.query(EventClass).filter(EventClass.is_builtin == True).all()
    custom = db.query(EventClass).filter(EventClass.created_by == user.user_id).all()
    logger.info(f"User {user.user_id} listed {len(builtin)} builtin and {len(custom)} custom event classes")
    return builtin + custom



@router.get('/{class_id}', response_model=EventClassResponse)
def get_event_class(
    class_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    event_class = db.query(EventClass).filter(EventClass.class_id == class_id).first()
    if not event_class:
        logger.warning(f"User {user.user_id} tried to get event class {class_id} that does not exist")
        raise HTTPException(status_code=404, detail="Event class not found")
    return event_class