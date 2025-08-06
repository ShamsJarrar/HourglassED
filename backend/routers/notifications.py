""""
User receives in-app notifications in the following cases:

1. From event invitation:
    - if they received an invitation
    - if their sent invitation was accepted

2. From friend requests:
    - if they received a request
    - if their request was accepted

3. (TO BE ADDED LATER)Before an event in a certain amount of time (remind_me_before)

"""


from fastapi import APIRouter, HTTPException, Depends, status, Response
from sqlalchemy.orm import Session
from dependencies import get_current_user, get_db
from logger import logger
from models.notification import Notification
from models.user import User
from schemas.notification import NotificationResponse
from typing import List


router = APIRouter(prefix='/notifications', tags=['Notifications'])


@router.get('/', response_model=List[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    notifications = db.query(Notification).filter(
        Notification.user_id == user.user_id
    ).order_by(Notification.created_at.desc()).all()

    logger.info(f"User {user.user_id} viewed their notifications")
    return notifications


@router.post('/mark-as-read/{notification_id}', status_code=status.HTTP_200_OK)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    notification = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.user_id == user.user_id
    ).first()

    if not notification:
        logger.warning(f"User {user.user_id} tried to mark a non-existent notification")
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.is_read:
        logger.warning(f"User {user.user_id} is trying to mark an already read notification")
        raise HTTPException(status_code=400, detail="Notification is already read")
    
    notification.is_read = True
    db.commit()
    logger.info(f"User {user.user_id} marked notification with id {notification_id} as read")
    return {"message": "Notification marked as read"}


