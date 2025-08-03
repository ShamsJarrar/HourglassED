from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from dependencies import get_current_user, get_db
from models.user import User
from models.event import Event
from models.event_invitation import EventInvitation, EventInvitationStatus
from models.friend import Friend
from schemas.event_invitation import EventInvitationCreate, EventInvitationResponse, EventInvitationResponseUpdate, EventInvitationWithEvent
from typing import List, Optional


router = APIRouter(prefix='/invitations', tags=['Event invitations'])


@router.post('/', response_model=EventInvitationResponse)
def invite_user_to_event(
    event_invite: EventInvitationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    event = db.query(Event).filter(Event.event_id == event_invite.event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event does not exist")
    
    # if the user does not own the event, they cannot invite others to it
    if event.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this event")
    
    # owner cannot invite themselves
    if event_invite.invited_user_id == user.user_id:
        raise HTTPException(status_code=400, detail="You cannot invite yourself")
    

    is_friend = db.query(Friend).filter(
        Friend.user_id == user.user_id,
        Friend.friend_id == event_invite.invited_user_id
    ).first()

    if not is_friend:
        raise HTTPException(status_code=403, detail="Can only invite friends")
    
    
    exists = db.query(EventInvitation).filter(
        EventInvitation.event_id == event_invite.event_id,
        EventInvitation.invited_user_id == event_invite.invited_user_id
    ).first()

    if exists:
        raise HTTPException(status_code=400, detail="User is already invited to this event")
    

    new_invitation = EventInvitation(
        event_id = event_invite.event_id,
        invited_user_id = event_invite.invited_user_id,
        status = EventInvitationStatus.pending,
    )

    db.add(new_invitation)
    db.commit()
    db.refresh(new_invitation)
    return new_invitation



@router.post('/respond', response_model=EventInvitationResponse)
def respond_to_event_invite(
    response: EventInvitationResponseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    event_invite = db.query(EventInvitation).filter(
        EventInvitation.invitation_id == response.invitation_id
    ).first()

    if not event_invite:
        raise HTTPException(status_code=404, detail="Invitation does not exist")
    
    if event_invite.invited_user_id != user.user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this invitation")
    
    if event_invite.status != EventInvitationStatus.pending:
        raise HTTPException(status_code=400, detail="Invite already accepted/rejected")
    
    event_invite.status = response.status
    db.commit()
    db.refresh(event_invite)
    return event_invite



@router.get('/received', response_model=List[EventInvitationWithEvent])
def get_received_invites(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    invites = db.query(EventInvitation).join(Event).join(User, Event.user).filter(
        EventInvitation.invited_user_id == user.user_id,
        EventInvitation.status == EventInvitationStatus.pending
    ).all()

    return invites



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
        raise HTTPException(status_code=404, detail="Invitation does not exist")
    
    if invitation.status != EventInvitationStatus.pending:
        raise HTTPException(status_code=400, detail="Invite already accepted, cannot delete")
    

    event = db.query(Event).filter(
        Event.event_id == invitation.event_id
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this invite")
    
    
    db.delete(invitation)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)



# TODO: add event_invitations status withdrawn, removed, expired