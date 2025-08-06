from models.notification import Notification
from sqlalchemy.orm import Session
from logger import logger


def create_notification(db: Session, user_id: int, message: str):
    logger.info(f"New notification being created for {user_id}")
    notification = Notification(user_id=user_id, message=message)
    db.add(notification)
    db.commit()