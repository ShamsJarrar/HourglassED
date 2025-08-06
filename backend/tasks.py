from celery_app import celery_app
from database import SessionLocal
from models.user import User
from models.event_invitation import EventInvitation, EventInvitationStatus
from models.event_class import EventClass
from models.event import Event
from datetime import datetime, UTC
from logger import logger


# if an event passed, then the invitation expires
@celery_app.task
def expire_passed_invitations():
    db = SessionLocal()

    try:
        now = datetime.now(UTC)

        expired_invitations = db.query(EventInvitation).join(Event).filter(
            Event.end_time < now,
            EventInvitation.status == EventInvitationStatus.pending
        ).all()

        cnt = 0
        for invite in expired_invitations:
            invite.status = EventInvitationStatus.expired
            cnt += 1
        
        db.commit()
        logger.info(f"{cnt} event invitations were expired")
    
    except Exception as e:
        db.rollback()
        logger.error(f"Celery faced an error expiring events: {e}")
    
    finally:
        db.close()