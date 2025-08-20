from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from logger import logger
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import random


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINS = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINS", 60))
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "hourglassed.calendar@gmail.com")


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


def generate_otp() -> str:
    otp = f"{random.randint(0, 999999):06}"
    logger.debug(f"Generated OTP: {otp}")
    return otp


def send_otp_email(email: str, otp: str):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject="Verify your email - HourglassED",
        plain_text_content=f"Your OTP code is: {otp}. It will expire in 10 minutes."
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"OTP email sent to {email} - status {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}")
        raise