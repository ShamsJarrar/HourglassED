from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional


try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


# not used since we are defaulting to UTC for now
def to_naive_utc(dt: datetime, tz_name: Optional[str] = None) -> datetime:
    """
    To convert a datetime object to a naive UTC datetime object as in the database.
    - If `dt` is naive and `tz_name` is provided: interpret dt as local tz_name, then convert to UTC and drop tzinfo.
    - If `dt` is naive and no tz_name: assume it is already UTC-naive; return as-is.
    - If `dt` is aware: convert to UTC and drop tzinfo.
    """

    if dt.tzinfo is None:
        if tz_name and ZoneInfo:
            local = dt.replace(tzinfo=ZoneInfo(tz_name))
            return local.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def now_utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)