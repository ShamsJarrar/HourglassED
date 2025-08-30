from __future__  import annotations
from sqlalchemy import func
from models.recurrence_series import RecurrenceSeries
from models.event import Event
from sqlalchemy.orm import Session
from .time import now_utc_naive
from datetime import datetime, timedelta
from typing import Iterable, Optional, Tuple, List
from dateutil.rrule import rrulestr


def _duration(start: datetime, end: datetime) -> timedelta:
    if end <= start:
        raise ValueError("End time must be after start time")
    return end - start


def _compute_window_end(start: datetime, recurrence_end: Optional[datetime], seed_months: int) -> datetime:
    horizon = start + timedelta(days=seed_months * 30)
    return min(recurrence_end, horizon) if recurrence_end else horizon


def _first_template_event(db: Session, series_id: int) -> Optional[Event]:
    return (
        db.query(Event)
        .filter(Event.series_id == series_id)
        .order_by(Event.start_time.asc())
        .first()
    )


def _max_existing_start(db: Session, series_id: int) -> Optional[datetime]:
    return (
        db.query(func.max(Event.start_time))
        .filter(Event.series_id == series_id)
        .scalar()
    )


def _generate_occurrences(
    series_rule: str,
    dstart: datetime,
    window_end: datetime
) -> Iterable[datetime]:

    rule = rrulestr(series_rule, dtstart=dstart)
    return rule.between(dstart, window_end, inc=True)


def create_series_and_seed(
    db: Session,
    *,
    user_id: int,
    event_type: int,
    title: str,
    header: Optional[str],
    start_time: datetime,
    end_time: datetime,
    timezone_name: str,
    recurrence_pattern: str,          
    recurrence_end: Optional[datetime] = None,
    seed_months: int = 6,
    color: str = "#FFD700",
    notes: Optional[str] = None,
) -> RecurrenceSeries:
    """
    Create a RecurrenceSeries and insert concrete Event rows for each occurrence
    up to a rolling window (or UNTIL/recurrence_end, whichever comes first).
    Expects input datetimes in *local tz of timezone_name* or aware datetimes;
    will save UTC-naive to DB and keep timezone field for display/expansion.
    """

    start_utc = start_time
    end_utc   = end_time
    until_utc = recurrence_end if recurrence_end else None

    duration = _duration(start_utc, end_utc)
    series = RecurrenceSeries(
        user_id=user_id,
        recurrence_pattern=recurrence_pattern,
        recurrence_end=until_utc
    )
    db.add(series)
    db.flush()

    window_end = _compute_window_end(start_utc, until_utc, seed_months)

    events: List[Event] = []
    for occ_start in _generate_occurrences(recurrence_pattern, start_utc, window_end):
        events.append(Event(
            event_type=event_type,
            header=header,
            title=title,
            start_time=occ_start,
            end_time=occ_start + duration,
            color=color,
            notes=notes,
            user_id=user_id,
            series_id=series.series_id,
            timezone="UTC",
            is_exception=False
        ))
    
    if not events:
        events.append(Event(
            event_type=event_type,
            header=header,
            title=title,
            start_time=start_utc,
            end_time=start_utc + duration,
            color=color,
            notes=notes,
            user_id=user_id,
            series_id=series.series_id,
            timezone="UTC",
            is_exception=False
        ))
    
    db.add_all(events)
    db.commit()
    db.refresh(series)
    return series


def reapply_series_from(
    db: Session,
    *,
    series_id: int,
    pivot: datetime,
    new_rrule: Optional[str] = None,
    new_recurrence_end: Optional[datetime] = None,
    window_months: int = 6,
) -> Optional[RecurrenceSeries]:
    """
    Reapply a recurrence rule to a series from `pivot` forward:
    - Optionally updates the RRULE and/or recurrence_end.
    - Deletes future non-exception rows starting at pivot.
    - Regenerates future non-exception rows to a rolling window.
    """

    series = db.get(RecurrenceSeries, series_id)
    if not series:
        return None

    template = _first_template_event(db, series_id)
    if not template:
        if new_rrule:
            series.recurrence_pattern = new_rrule
        if new_recurrence_end is not None:
            series.recurrence_end = new_recurrence_end
        db.commit()
        db.refresh(series)
        return series

    if new_rrule:
        series.recurrence_pattern = new_rrule
    if new_recurrence_end is not None:
        series.recurrence_end = new_recurrence_end

    pivot_utc = pivot

    (db.query(Event)
       .filter(Event.series_id == series_id,
               Event.start_time >= pivot_utc,
               Event.is_exception == False)
       .delete(synchronize_session=False))

    duration = _duration(template.start_time, template.end_time)
    until_utc = series.recurrence_end
    window_end = _compute_window_end(pivot_utc, until_utc, window_months)

    new_events: List[Event] = []
    for occ_start in _generate_occurrences(series.recurrence_pattern, pivot_utc, window_end):
        new_events.append(Event(
            event_type=template.event_type,
            header=template.header,
            title=template.title,
            start_time=occ_start,
            end_time=occ_start + duration,
            color=template.color,
            notes=None,
            user_id=template.user_id,
            series_id=series.series_id,
            timezone="UTC",
            is_exception=False
        ))
    if new_events:
        db.add_all(new_events)

    db.commit()
    db.refresh(series)
    return series


def delete_series(db: Session, series_id: int) -> bool:
    """
    Delete a series (events will cascade).
    """
    series = db.get(RecurrenceSeries, series_id)
    if not series:
        return False
    db.delete(series)
    db.commit()
    return True


def ensure_series_window(
    db: Session,
    *,
    series_id: int,
    window_months: int = 3
) -> bool:
    """
    Ensure a series has occurrences up to now + window_months.
    Only adds missing future non-exception rows; does not touch exceptions.
    """
    
    template = _first_template_event(db, series_id)
    if not template:
        return False

    last_start = _max_existing_start(db, series_id)
    if last_start is None:
        next_seed_start = template.start_time
    else:
        next_seed_start = last_start + timedelta(seconds=1)


    until_utc = template.series.recurrence_end if template.series else None
    target_end = _compute_window_end(now_utc_naive(), until_utc, window_months)

    if next_seed_start > target_end:
        return True  

    new_events: List[Event] = []
    duration = _duration(template.start_time, template.end_time)
    for occ_start in _generate_occurrences(template.series.recurrence_pattern, next_seed_start, target_end):
        new_events.append(Event(
            event_type=template.event_type,
            header=template.header,
            title=template.title,
            start_time=occ_start,
            end_time=occ_start + duration,
            color=template.color,
            notes=None,
            user_id=template.user_id,
            series_id=template.series_id,
            timezone="UTC",
            is_exception=False
        ))

    if new_events:
        db.add_all(new_events)
        db.commit()

    return True