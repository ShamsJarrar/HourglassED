from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate, UserLogin, UserResponse, OTPVerifyRequest
from schemas.token import TokenWithUserResponse
from dependencies import get_db
from utils.security import hash_password, verify_password, create_access_token, generate_otp, send_otp_email
from utils.helpers import normalize_string
from jose import JWTError, jwt
from pydantic import EmailStr
from logger import logger
from datetime import datetime, timezone, timedelta


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
    otp = generate_otp()
    expiration = datetime.now(timezone.utc) + timedelta(minutes=10)

    new_user = User(
        email=email,
        name=name,
        password=hashed_password,
        is_verified=False,
        otp_code=otp,
        otp_expiration=expiration
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    send_otp_email(email, otp)

    logger.info(f"New user registered (verification pending): {new_user.user_id} ({email})")
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


@router.post("/verify-email-otp")
def verify_email_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    email = normalize_string(request.email)
    user = db.query(User).filter(User.email == email).first()

    if not user:
        logger.warning(f"Verification attempt for non-existent email: {email}")
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        logger.info(f"User {user.user_id} tried to verify already verified email")
        return {"message": "Email already verified."}
    
    if not user.otp_code or user.otp_code != request.otp:
        logger.warning(f"Invalid OTP for email: {email}")
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    otp_exp = user.otp_expiration.replace(tzinfo=timezone.utc)
    if otp_exp < datetime.now(timezone.utc):
        logger.warning(f"OTP expired for email: {email}")
        raise HTTPException(status_code=400, detail="OTP expired")
    

    user.is_verified = True
    user.otp_code = None
    user.otp_expiration = None
    db.commit()
    db.refresh(user)

    logger.info(f"User {user.user_id} verified their email with OTP")
    return {"message": "✅ Email successfully verified. You can now log in."}


@router.post('/resend-otp')
def resend_otp(email: EmailStr, db: Session = Depends(get_db)):
    email = normalize_string(email)
    user = db.query(User).filter(User.email == email).first()

    if not user:
        logger.warning(f"Verification attempt for non-existent email: {email}")
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        logger.info(f"User {user.user_id} tried to verify already verified email")
        return {"message": "Email already verified."}
    

    otp = generate_otp()
    user.otp_code = otp
    user.otp_expiration = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()
    db.refresh(user)

    send_otp_email(email, otp)

    logger.info(f"OTP resent to {email}")
    return {"message": "OTP resent."}

