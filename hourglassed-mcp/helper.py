from datetime import datetime, timezone
from typing import Optional, List, Tuple


def _parse_iso(s: str) -> datetime:
    # robustly handle "Z"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _iso(dt: datetime) -> str:
    # ensure UTC and output Z to match frontend toISOString()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    s = dt.isoformat(timespec="milliseconds")
    return s[:-6] + "Z" if s.endswith("+00:00") else s


def _as_query_param(name: str, values: Optional[List[str]]) -> Optional[Tuple[str, str]]:
    if not values:
        return []
    return [(name, value) for value in values]