from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user
from utils.helpers import normalize_string
from schemas.friend_request import FriendRequestCreate, FriendRequestResponse
from schemas.friend import FriendResponse
from models.friend_request import FriendRequest, FriendRequestStatus
from models.user import User
from models.friend import Friend
from models.friend_request import FriendRequest


router = APIRouter(prefix='/friends', tags=['Friends'])



@router.post('/friend-request', response_model=FriendRequestResponse)
def send_friend_request(
    req: FriendRequestCreate, 
    db: Session = Depends(get_db),
    cur_user: User = Depends(get_current_user)
):
    
    receiver_email = normalize_string(req.receiver_email)
    if receiver_email == cur_user.email:
        raise HTTPException(status_code=400, detail="Cannot friend request yourself")
    

    receiver = db.query(User).filter(User.email == receiver_email).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")
    

    # friendship adds two rows to db, so checking in one direction is enough
    friendship_exists = db.query(Friend).filter(
        Friend.friend_id == receiver.user_id, 
        Friend.user_id == cur_user.user_id
        ).first()
    if friendship_exists:
        raise HTTPException(status_code=400, detail="Already friends")
    

    request_exists = db.query(FriendRequest).filter(
        FriendRequest.status == FriendRequestStatus.pending,
        ((FriendRequest.sender_id == cur_user.user_id) & (FriendRequest.receiver_id == receiver.user_id)) |
        ((FriendRequest.sender_id == receiver.user_id) & (FriendRequest.receiver_id == cur_user.user_id))
        ).first()
    if request_exists:
        raise HTTPException(status_code=400, detail="Already requested")
    

    new_request = FriendRequest(
        sender_id=cur_user.user_id,
        receiver_id=receiver.user_id
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request



@router.post('/friend-request/{request_id}/accept')
def accept_request(
    request_id: int,
    db: Session = Depends(get_db),
    cur_user: User = Depends(get_current_user)
):
    
    friend_req = db.query(FriendRequest).filter(
        FriendRequest.request_id == request_id
    ).first()
    if not friend_req:
        raise HTTPException(status_code=404, detail="Friend request does not exist")
    
    if friend_req.receiver_id != cur_user.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    if friend_req.status != FriendRequestStatus.pending:
        raise HTTPException(status_code=400, detail="Request already accepted/rejected")


    friend_req.status = FriendRequestStatus.accepted
    db.commit()
    db.refresh(friend_req)


    db.add_all([
        Friend(user_id=friend_req.sender_id, friend_id=friend_req.receiver_id),
        Friend(user_id=friend_req.receiver_id, friend_id=friend_req.sender_id)
    ])
    db.commit()

    return {"message":"Friend request accepted"}



@router.post('/friend-request/{request_id}/reject')
def reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    cur_user: User = Depends(get_current_user)
):
    
    friend_req = db.query(FriendRequest).filter(
        FriendRequest.request_id == request_id
    ).first()
    if not friend_req:
        raise HTTPException(status_code=404, detail="Friend request does not exist")
    
    if friend_req.receiver_id != cur_user.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    if friend_req.status != FriendRequestStatus.pending:
        raise HTTPException(status_code=400, detail="Request already accepted/rejected")


    friend_req.status = FriendRequestStatus.rejected
    db.commit()

    return {"message":"Friend request rejected"}


@router.get('/friend-requests/received', response_model=list[FriendRequestResponse])
def received_requests(
    db: Session = Depends(get_db),
    cur_user: User = Depends(get_current_user)
):

    friend_requests = db.query(FriendRequest).filter(
        FriendRequest.receiver_id == cur_user.user_id,
        FriendRequest.status == FriendRequestStatus.pending
    ).all()
    return friend_requests


@router.get('/friend-requests/sent', response_model=list[FriendRequestResponse])
def sent_requests(
    db: Session = Depends(get_db),
    cur_user: User = Depends(get_current_user)
):
    
    friend_requests = db.query(FriendRequest).filter(
        FriendRequest.sender_id == cur_user.user_id,
        FriendRequest.status == FriendRequestStatus.pending
    ).all()
    return friend_requests


@router.get('/friends', response_model=list[FriendResponse])
def view_friends(
    db: Session = Depends(get_db),
    cur_user: User = Depends(get_current_user)
):
    
    friends = db.query(Friend).filter(
        Friend.user_id == cur_user.user_id,
    ).all()
    return friends


# TODO: Add unfriend functionality
# TODO: Delete request if still pending
# TODO: Add notifications?