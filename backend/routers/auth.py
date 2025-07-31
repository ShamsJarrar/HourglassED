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

router = APIRouter(prefix='/auth', tags=["Auth"])


@router.post('/register', response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):

    email = normalize_string(user.email)
    exists = db.query(User).filter(User.email == email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email registered already")
    
    hashed_password = hash_password(user.password)
    new_user = User(email=email, name=user.name, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # to add user_id

    token = create_email_verification_token(new_user.user_id)
    send_verification_email(email, token)

    return new_user


@router.post('/login', response_model=TokenWithUserResponse)
def login(info: UserLogin, db: Session = Depends(get_db)):

    email = normalize_string(info.email)
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(info.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in.")

    token = create_access_token(data={"sub": str(user.user_id)})

    return TokenWithUserResponse(access_token=token, user=user)


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        return {"message": "Email already verified."}
    
    user.is_verified = True
    db.commit()
    return {"message": "✅ Email successfully verified. You can now log in."}


@router.post('/resend-verification')
def resend_verfication(email: EmailStr, db: Session = Depends(get_db)):
    email = normalize_string(email)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered.")
    if user.is_verified:
        return {"message": "Email already verified."}

    token = create_email_verification_token(user.user_id)

    print(f"[RESEND] Verification link: http://localhost:8000/auth/verify-email?token={token}")

    return {"message": "Verification email resent."}