from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from dependencies import get_current_user, get_db
from models.user import User
from models.event import Event
from models.event_invitation import EventInvitation, EventInvitationStatus
from models.friend import Friend
from schemas.event_invitation import EventInvitationCreate, EventInvitationResponse, EventInvitationResponseUpdate, EventInvitationWithEvent
from typing import List, Optional
from logger import logger
from tasks import expire_passed_invitations


router = APIRouter(prefix='/invitations', tags=['Event invitations'])


@router.post('/', response_model=EventInvitationResponse)
def invite_user_to_event(
    event_invite: EventInvitationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    event = db.query(Event).filter(Event.event_id == event_invite.event_id).first()

    if not event:
        logger.warning(f"User {user.user_id} tried to access a non-existent event")
        raise HTTPException(status_code=404, detail="Event does not exist")
    
    # if the user does not own the event, they cannot invite others to it
    if event.user_id != user.user_id:
        logger.warning(f"User {user.user_id} is not authorized to invite to event {event_invite.event_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to access this event")
    
    # owner cannot invite themselves
    if event_invite.invited_user_id == user.user_id:
        logger.warning(f"User {user.user_id} attempted to invite themselves to their own event")
        raise HTTPException(status_code=400, detail="You cannot invite yourself")
    

    is_friend = db.query(Friend).filter(
        Friend.user_id == user.user_id,
        Friend.friend_id == event_invite.invited_user_id
    ).first()

    if not is_friend:
        logger.warning(f"User {user.user_id} attempted to invite non-friend {event_invite.invited_user_id}")
        raise HTTPException(status_code=403, detail="Can only invite friends")
    
    
    exists = db.query(EventInvitation).filter(
        EventInvitation.event_id == event_invite.event_id,
        EventInvitation.invited_user_id == event_invite.invited_user_id
    ).first()

    if exists:
        logger.warning(f"User {user.user_id} tried to invite user {event_invite.invited_user_id} who is already invited")
        raise HTTPException(status_code=400, detail="User is already invited to this event")
    

    new_invitation = EventInvitation(
        event_id = event_invite.event_id,
        invited_user_id = event_invite.invited_user_id,
        status = EventInvitationStatus.pending,
    )

    db.add(new_invitation)
    db.commit()
    db.refresh(new_invitation)
    logger.info(f"User {user.user_id} invited user {event_invite.invited_user_id} to event {event_invite.event_id}")
    return new_invitation



@router.post('/respond', response_model=EventInvitationResponse)
def respond_to_event_invite(
    answer: EventInvitationResponseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    event_invite = db.query(EventInvitation).filter(
        EventInvitation.invitation_id == answer.invitation_id
    ).first()

    if not event_invite:
        logger.warning(f"User {user.user_id} tried to respond to non-existent invitation {answer.invitation_id}")
        raise HTTPException(status_code=404, detail="Invitation does not exist")
    
    if event_invite.invited_user_id != user.user_id:
        logger.warning(f"User {user.user_id} is not authorized to access this invitation")
        raise HTTPException(status_code=403, detail="You are not authorized to access this invitation")
    
    if event_invite.status != EventInvitationStatus.pending:
        logger.warning(f"User {user.user_id} tried to respond to invitation {answer.invitation_id} with status {event_invite.status}")
        raise HTTPException(status_code=400, detail="Invite already accepted/rejected/withdrawn/expired")
    
    if (answer.response != EventInvitationStatus.accepted) and\
        (answer.response != EventInvitationStatus.rejected):
        logger.warning(f"User {user.user_id} did not respond with accept/reject to invite {answer.invitation_id}")
        raise HTTPException(status_code=400, detail="Can only accept or reject invite")


    event_invite.status = answer.response
    db.commit()
    db.refresh(event_invite)
    logger.info(f"User {user.user_id} responded to invitation {answer.invitation_id} with status {answer.response}")
    return event_invite



@router.get('/received', response_model=List[EventInvitationWithEvent])
def get_received_invites(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    query = db.query(EventInvitation).join(Event).join(User, Event.user).filter(
        EventInvitation.invited_user_id == user.user_id,
        EventInvitation.status == EventInvitationStatus.pending
    )

    logger.debug(f"User {user.user_id} fetched pending received invitations")
    return query.all()



@router.get('/sent', response_model=List[EventInvitationWithEvent])
def get_sent_invites(
    event_id: Optional[int] = Query(None),
    status: Optional[EventInvitationStatus] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    query = db.query(EventInvitation).join(Event).join(User, EventInvitation.invited_user).filter(
        Event.user_id == user.user_id
    )

    if event_id:
        query = query.filter(EventInvitation.event_id == event_id)

    if status:
        query = query.filter(EventInvitation.status == status)
    
    logger.debug(f"User {user.user_id} fetched sent invitations with event_id={event_id}, status={status}")
    return query.all()



@router.delete('/{invitation_id}', status_code=status.HTTP_204_NO_CONTENT)
def cancel_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    invitation = db.query(EventInvitation).filter(
        EventInvitation.invitation_id == invitation_id,
    ).first()

    if not invitation:
        logger.warning(f"User {user.user_id} tried to cancel non-existent invitation {invitation_id}")
        raise HTTPException(status_code=404, detail="Invitation does not exist")
    
    if invitation.status != EventInvitationStatus.pending:
        logger.warning(f"User {user.user_id} tried to cancel invitation {invitation_id} which is not pending")
        raise HTTPException(status_code=400, detail="Invite already accepted, cannot delete")
    

    event = db.query(Event).filter(
        Event.event_id == invitation.event_id
    ).first()

    if not event:
        logger.warning(f"User {user.user_id} tried to cancel invite {invitation_id} for a non-existent event")
        raise HTTPException(status_code=404, detail="Event not found")

    if event.user_id != user.user_id:
        logger.warning(f"User {user.user_id} is not authorized to cancel invitation {invitation_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to delete this invite")
    
    
    invitation.status = EventInvitationStatus.withdrawn
    db.commit()
    db.refresh(invitation)
    logger.info(f"User {user.user_id} withdrew invitation {invitation_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# endpoint for testing if celery works correctly
# can be commented when celery beat is used
@router.post("/expire-invitations-background")
def trigger_expiration_task():
    expire_passed_invitations.delay()
    return {"message": "Event invitation expiration task triggered in background"}