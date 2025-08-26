from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session, joinedload
from dependencies import get_db, get_current_user
from utils.helpers import normalize_string
from utils.notifications import create_notification
from schemas.friend_request import FriendRequestCreate, FriendRequestResponse, FriendRequestResponseWithEmails
from schemas.friend import FriendResponse
from models.friend_request import FriendRequest, FriendRequestStatus
from models.user import User
from models.friend import Friend
from logger import logger


router = APIRouter(prefix='/friends', tags=['Friends'])



@router.post('/friend-request', response_model=FriendRequestResponse)
def send_friend_request(
    req: FriendRequestCreate, 
    db: Session = Depends(get_db),
    cur_user: User = Depends(get_current_user)
):
    
    receiver_email = normalize_string(req.receiver_email)
    if receiver_email == cur_user.email:
        logger.warning(f"User {cur_user.user_id} tried to send a friend request to themselves")
        raise HTTPException(status_code=400, detail="Cannot friend request yourself")
    

    receiver = db.query(User).filter(User.email == receiver_email).first()
    if not receiver:
        logger.warning(f"Receiver user is non-existent")
        raise HTTPException(status_code=404, detail="User not found")
    

    # friendship adds two rows to db, so checking in one direction is enough
    friendship_exists = db.query(Friend).filter(
        Friend.friend_id == receiver.user_id, 
        Friend.user_id == cur_user.user_id
        ).first()
    if friendship_exists:
        logger.warning(f"User {cur_user.user_id} tried to send friend request to a friend!")
        raise HTTPException(status_code=400, detail="Already friends")
    

    request_exists = db.query(FriendRequest).filter(
        FriendRequest.status == FriendRequestStatus.pending,
        ((FriendRequest.sender_id == cur_user.user_id) & (FriendRequest.receiver_id == receiver.user_id)) |
        ((FriendRequest.sender_id == receiver.user_id) & (FriendRequest.receiver_id == cur_user.user_id))
        ).first()
    if request_exists:
        logger.warning(f"User {cur_user.user_id} already sent a friend request before")
        raise HTTPException(status_code=400, detail="Already requested")
    

    new_request = FriendRequest(
        sender_id=cur_user.user_id,
        receiver_id=receiver.user_id
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)


    try:
        create_notification(
            db = db,
            user_id = receiver.user_id,
            message = f"{cur_user.name} has sent you a friend request"
        )
    except Exception as e:
        logger.error(f"Error while creating notification {e}")
    

    logger.info(f"User {cur_user.user_id} sent friend request to {receiver.user_id}")
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
        logger.warning(f"User {cur_user.user_id} tried to accept a non-existent friend request")
        raise HTTPException(status_code=404, detail="Friend request does not exist")
    
    if friend_req.receiver_id != cur_user.user_id:
        logger.warning(f"User {cur_user.user_id} is not authorized to access friend request {request_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    if friend_req.status != FriendRequestStatus.pending:
        logger.warning(f"User {cur_user.user_id} tried to respond to an already accepted/rejected request")
        raise HTTPException(status_code=400, detail="Request already accepted/rejected")


    friend_req.status = FriendRequestStatus.accepted
    db.commit()
    db.refresh(friend_req)


    db.add_all([
        Friend(user_id=friend_req.sender_id, friend_id=friend_req.receiver_id),
        Friend(user_id=friend_req.receiver_id, friend_id=friend_req.sender_id)
    ])
    db.commit()


    try:
        create_notification(
            db = db,
            user_id = friend_req.sender_id,
            message = f"{cur_user.name} has accepted your friend request"
        )
    except Exception as e:
        logger.error(f"Error while creating notification {e}")


    logger.info(f"User {cur_user.user_id} accepted friend request {request_id} from {friend_req.sender_id}")
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
        logger.warning(f"User {cur_user.user_id} tried to reject a non-existent friend request")
        raise HTTPException(status_code=404, detail="Friend request does not exist")
    
    if friend_req.receiver_id != cur_user.user_id:
        logger.warning(f"User {cur_user.user_id} is not authorized to access friend request {request_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")
    
    if friend_req.status != FriendRequestStatus.pending:
        logger.warning(f"User {cur_user.user_id} tried to respond to an already accepted/rejected request")
        raise HTTPException(status_code=400, detail="Request already accepted/rejected")


    friend_req.status = FriendRequestStatus.rejected
    db.commit()

    logger.info(f"User {cur_user.user_id} rejected friend request {request_id} from {friend_req.sender_id}")
    return {"message":"Friend request rejected"}


@router.get('/friend-requests/received', response_model=list[FriendRequestResponseWithEmails])
def received_requests(
    db: Session = Depends(get_db),
    cur_user: User = Depends(get_current_user)
):

    friend_requests = db.query(FriendRequest).options(
        joinedload(FriendRequest.sender),
        joinedload(FriendRequest.receiver)
    ).filter(
        FriendRequest.receiver_id == cur_user.user_id,
        FriendRequest.status == FriendRequestStatus.pending
    ).all()

    response = [
        FriendRequestResponseWithEmails(
            request_id=fr.request_id,
            sender_id=fr.sender_id,
            receiver_id=fr.receiver_id,
            status=fr.status,
            created_at=fr.created_at,
            sender_email=fr.sender.email,
            receiver_email=fr.receiver.email
        )
        for fr in friend_requests
    ]

    logger.debug(f"User {cur_user.user_id} fetched received friend requests")
    return response


@router.get('/friend-requests/sent', response_model=list[FriendRequestResponseWithEmails])
def sent_requests(
    db: Session = Depends(get_db),
    cur_user: User = Depends(get_current_user)
):
    
    friend_requests = db.query(FriendRequest).options(
        joinedload(FriendRequest.sender),
        joinedload(FriendRequest.receiver)
    ).filter(
        FriendRequest.sender_id == cur_user.user_id,
        FriendRequest.status == FriendRequestStatus.pending
    ).all()

    response = [
        FriendRequestResponseWithEmails(
            request_id=fr.request_id,
            sender_id=fr.sender_id,
            receiver_id=fr.receiver_id,
            status=fr.status,
            created_at=fr.created_at,
            sender_email=fr.sender.email,
            receiver_email=fr.receiver.email
        )
        for fr in friend_requests
    ]

    logger.debug(f"User {cur_user.user_id} fetched sent friend requests")
    return response


@router.get('/friends', response_model=list[FriendResponse])
def view_friends(
    db: Session = Depends(get_db),
    cur_user: User = Depends(get_current_user)
):
    
    friends = db.query(Friend).options(
        joinedload(Friend.friend_user)
    ).filter(
        Friend.user_id == cur_user.user_id
    ).all()

    friend_responses = [
        FriendResponse(
            friend_id=fr.friend_id,
            friend_name=fr.friend_user.name,
            friend_email=fr.friend_user.email
        )
        for fr in friends
    ]

    logger.debug(f"User {cur_user.user_id} fetched friend list")
    return friend_responses



@router.get('/friends/{friend_id}', response_model=FriendResponse)
def view_friend(
    friend_id: int,
    db: Session = Depends(get_db),
    cur_user: User = Depends(get_current_user)
):

    friendship = db.query(Friend).options(
        joinedload(Friend.friend_user)
    ).filter(
        Friend.user_id == cur_user.user_id,
        Friend.friend_id == friend_id
    ).first()

    if not friendship:
        logger.warning(f"User {cur_user.user_id} requested non-existent friendship {friend_id}")
        raise HTTPException(status_code=404, detail="Friendship not found")

    friend_response = FriendResponse(
        friend_id=friendship.friend_id,
        friend_name=friendship.friend_user.name,
        friend_email=friendship.friend_user.email
    )

    logger.debug(f"User {cur_user.user_id} fetched friend user {friend_id}")
    return friend_response


# request sender can unsend request if it is still pending
@router.delete('/friend-request/{request_id}/unsend', status_code=status.HTTP_204_NO_CONTENT)
def unsend_friend_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    friend_request = db.query(FriendRequest).filter(
        FriendRequest.request_id == request_id
    ).first()

    if not friend_request:
        logger.warning(f"User {user.user_id} tried to unsend a non-existent friend request")
        raise HTTPException(status_code=404, detail="Friend request does not exist")
    
    if friend_request.sender_id != user.user_id:
        logger.warning(f"User {user.user_id} is not authorized to access friend request {request_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to delete this friend request")
    
    if friend_request.status != FriendRequestStatus.pending:
        logger.warning(f"User {user.user_id} tried to respond to an already accepted/rejected request")
        raise HTTPException(status_code=400, detail="Friend request already accepted/rejected")
    

    db.delete(friend_request)
    db.commit()
    logger.info(f"User {user.user_id} unsent friend request to {friend_request.receiver_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete('/unfriend/{friend_id}', status_code=status.HTTP_204_NO_CONTENT)
def unfriend(
    friend_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    
    friendship = db.query(Friend).filter(
        Friend.friend_id == friend_id,
        Friend.user_id == user.user_id
    ).first()

    recursive_friendship = db.query(Friend).filter(
        Friend.friend_id == user.user_id,
        Friend.user_id == friend_id
    ).first()

    if not friendship or not recursive_friendship:
        logger.warning(f"User {user.user_id} tried to unsend a non-existent friend request")
        raise HTTPException(status_code=404, detail="Friendship does not exist")
    

    db.delete(friendship)
    db.delete(recursive_friendship)
    db.commit()
    logger.info(f"User {user.user_id} unfriended {friend_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


