from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate, UserLogin, UserResponse
from schemas.token import TokenWithUserResponse
from dependencies import get_db
from utils.security import hash_password, verify_password, create_access_token, create_email_verification_token, send_verification_email, decode_access_token
from utils.helpers import normalize_string
from jose import JWTError, jwt
from pydantic import EmailStr
from logger import logger


router = APIRouter(prefix='/auth', tags=["Auth"])


@router.post('/register', response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):

    email = normalize_string(user.email)
    name = normalize_string(user.name)
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        logger.warning(f"Attempted registration with already registered email: {email}")
        raise HTTPException(status_code=400, detail="Email registered already")
    
    hashed_password = hash_password(user.password)
    new_user = User(email=email, name=name, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # to add user_id

    token = create_email_verification_token(new_user.user_id)
    send_verification_email(email, token)

    logger.info(f"New user registered: {new_user.user_id} ({email})")
    return new_user


@router.post('/login', response_model=TokenWithUserResponse)
def login(info: UserLogin, db: Session = Depends(get_db)):

    email = normalize_string(info.email)
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(info.password, user.password):
        logger.warning(f"Failed login attempt for email: {email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_verified:
        logger.warning(f"Login attempt to unverified account: {email}")
        raise HTTPException(status_code=403, detail="Please verify your email before logging in.")

    token = create_access_token(data={"sub": str(user.user_id)})

    logger.info(f"User {user.user_id} logged in")
    return TokenWithUserResponse(access_token=token, user=user)


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except JWTError:
        logger.warning("Invalid or expired email verification token used")
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        logger.warning(f"Verification attempt for non-existent user ID: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        logger.info(f"User {user.user_id} tried to verify already verified email")
        return {"message": "Email already verified."}
    
    user.is_verified = True
    db.commit()
    logger.info(f"User {user.user_id} verified their email")
    return {"message": "✅ Email successfully verified. You can now log in."}


@router.post('/resend-verification')
def resend_verfication(email: EmailStr, db: Session = Depends(get_db)):
    email = normalize_string(email)
    user = db.query(User).filter(User.email == email).first()

    if not user:
        logger.warning(f"Resend verification attempted for non-existent email: {email}")
        raise HTTPException(status_code=404, detail="Email not registered.")
    
    if user.is_verified:
        logger.info(f"Resend requested for already verified email: {email}")
        return {"message": "Email already verified."}

    token = create_email_verification_token(user.user_id)

    # temp link message
    print(f"[RESEND] Verification link: http://localhost:8000/auth/verify-email?token={token}")
    logger.info(f"Resent verification email to {email}")
    return {"message": "Verification email resent."}