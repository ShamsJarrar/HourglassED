from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPAuthorizationCredentials
from jose import JWTError
from utils.security import decode_access_token
from schemas.token import TokenPayload
from models.user import User


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# TODO: uncomment when testing is done
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# for testing using swagger, adding a temp endpoint to send token manually
# instead of changing reponse schema
from fastapi.security import HTTPBearer
oauth2_scheme = HTTPBearer()

def get_current_user(
        token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
    )

    try:
        token = token.credentials
        payload = decode_access_token(token)
        token_data = TokenPayload(**payload)
    except (JWTError, ValueError):
        raise credentials_exception
    
    user = db.query(User).filter(User.user_id == int(token_data.sub)).first()
    if not user:
        raise credentials_exception
    return user
