from typing import Optional

_access_token: Optional[str] = None

def set_access_token(token: str) -> None:
    global _access_token
    _access_token = token

def clear_access_token() -> None:
    global _access_token
    _access_token = None

def get_auth_header() -> dict[str, str]:
    """Return authorization header with bearer token to match backend authentication"""
    if not _access_token:
        return {}
    return {"Authorization": f"Bearer {_access_token}"}