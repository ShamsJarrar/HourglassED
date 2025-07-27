from pydantic import BaseModel
from schemas.user import UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithUserResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str
    exp: int

