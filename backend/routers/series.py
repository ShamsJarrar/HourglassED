from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from dependencies import get_db, get_current_user
from models.user import User
from models.recurrence_series import RecurrenceSeries
from models.event import Event
from schemas.recurrence_series import RecurrenceSeriesCreate, RecurrenceSeriesResponse, RecurrenceSeriesUpdate
from schemas.event import EventCreate
from utils.helpers import get_event_class
from utils.recurrence import create_series_and_seed, reapply_series_from
from logger import logger
from datetime import datetime, timezone
from typing import Optional


router = APIRouter(prefix="/series", tags=["Recurrence Series"])


@router.post("/create", response_model=RecurrenceSeriesResponse)
def create_Series(
    recurrence: RecurrenceSeriesCreate,
    event: EventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    event_class = get_event_class(event.event_type, db, user)

    if event.start_time >= event.end_time:
        logger.warning(f"User {user.user_id} added invalid start and end times when creating a series")
        raise HTTPException(status_code=400, detail="start_time must be before end_time")
    
    series = create_series_and_seed(
        db=db,
        user_id=user.user_id,
        event_type = event_class.class_id,
        title = event.title,
        header = event.header,
        start_time = event.start_time,
        end_time = event.end_time,
        timezone_name = event.timezone,
        recurrence_pattern = recurrence.recurrence_pattern,
        recurrence_end = recurrence.recurrence_end,
        color = event.color,
        notes = event.notes
    )

    logger.info(f"User {user.user_id} created series {series.series_id}")
    return series



@router.get("/{series_id}", response_model=RecurrenceSeriesResponse)
def get_series(
    series_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    series = db.query(RecurrenceSeries).filter(
        RecurrenceSeries.series_id == series_id
    ).first()

    if not series:
        logger.warning(f"User {user.user_id} tried to access a non-existent series")
        raise HTTPException(status_code=404, detail="Series not found")

    if series.user_id != user.user_id:
        logger.warning(f"User {user.user_id} is not authorized to access series {series.series_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to access this series")

    return series


@router.patch("/{series_id}", response_model=RecurrenceSeriesResponse)
def update_series_from_pivot(
    series_id: int,
    updated_info: RecurrenceSeriesUpdate,
    pivot: Optional[datetime] = Query(None, description="when ommited, uses current UTC time"),
    months: int = Query(6, description="how many months to generate"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    series = db.query(RecurrenceSeries).filter(
        RecurrenceSeries.series_id == series_id
    ).first()

    if not series:
        logger.warning(f"User {user.user_id} tried to access a non-existent series")
        raise HTTPException(status_code=404, detail="Series not found")
    
    if series.user_id != user.user_id:
        logger.warning(f"User {user.user_id} is not authorized to edit series {series.series_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to edit this series")

    # Normalize pivot to UTC-naive for DB comparisons
    if pivot is None:
        pivot = datetime.now(timezone.utc)
    if pivot.tzinfo is not None:
        pivot = pivot.astimezone(timezone.utc).replace(tzinfo=None)
    
    # Normalize updated recurrence_end to UTC-naive if provided
    if updated_info.recurrence_end is not None and getattr(updated_info.recurrence_end, 'tzinfo', None) is not None:
        updated_info.recurrence_end = updated_info.recurrence_end.astimezone(timezone.utc).replace(tzinfo=None)

    updated_series = reapply_series_from(
        db=db,
        series_id=series_id,
        pivot=pivot,
        new_rrule=updated_info.recurrence_pattern,
        new_recurrence_end=updated_info.recurrence_end,
        window_months=months
    )

    if not updated_series:
        logger.warning(f"User {user.user_id} tried to update a series but series not found")
        HTTPException(status_code=400, detail="Failed to update series because series not found")
    

    logger.info(f"User {user.user_id} updated series {series_id} from pivot {pivot.isoformat()}")
    return updated_series



@router.delete("/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_series(
    series_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    series = db.query(RecurrenceSeries).filter(
        RecurrenceSeries.series_id == series_id
    ).first()

    if not series:
        logger.warning(f"User {user.user_id} tried to access a non-existent series")
        raise HTTPException(status_code=404, detail="Series not found")
    
    if series.user_id != user.user_id:
        logger.warning(f"User {user.user_id} is not authorized to delete series {series.series_id}")
        raise HTTPException(status_code=403, detail="You are not authorized to delete this series")
    

    db.delete(series)
    db.commit()
    logger.info(f"User {user.user_id} deleted series {series_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

