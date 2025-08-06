from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from logger import logger


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINS = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINS", 60))

# init pwd hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# pwd hashing
def hash_password(password: str) -> str:
    logger.debug("Hashing password")
    return pwd_context.hash(password)

def verify_password(og_password: str, hashed_password: str) -> bool:
    logger.debug("Verifying password")
    return pwd_context.verify(og_password, hashed_password)


# JWT tokens
def create_access_token(data: dict) -> str:
    logger.debug("Creating access token for data: %s", data)
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug("Token decoded successfully")
        return payload
    except JWTError as e:
        logger.error("Failed to decode token: %s", str(e))
        raise JWTError("Invalid token") from e


# email verification
def create_email_verification_token(user_id: int) -> str:
    logger.debug("Creating email verification token for user_id: %s", user_id)
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {
        "sub": str(user_id),
        "exp": expire.timestamp()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# TODO: Integrate email verification api later
def send_verification_email(email: str, token: str):
    logger.info(f"[MOCK] Verification email triggered for {email}")
    link = f"http://localhost:8000/auth/verify-email?token={token}"
    print(f"[MOCK] Verification link for {email}: {link}")