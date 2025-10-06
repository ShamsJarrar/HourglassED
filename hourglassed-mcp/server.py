from mcp.server.fastmcp import FastMCP
from schemas import EventCreate, EventResponse, RecurrenceSeriesCreate, RecurrenceSeriesResponse
from helper import _parse_iso, _iso, _as_query_param
from auth import get_auth_header, set_access_token
from httpx import AsyncClient, HTTPStatusError
from typing import Optional, List
from dotenv import load_dotenv
import os


mcp = FastMCP("hourglassed-calendar-mcp", host="127.0.0.1", port=8765)

load_dotenv()
HOURGLASSED_BACKEND_URL = os.getenv("HOURGLASSED_BACKEND_URL")


@mcp.tool()
async def pass_access_token(access_token: str) -> str:
    """
    Store the user's access token passed from the client
    to be used for authentication with the backend.

    Args:
        access_token: The user's access token passed from the client

    Returns:
        A message indicating that the access token is set successfully
    """
    set_access_token(access_token)
    return "Access token is set successfully"



@mcp.tool()
async def get_events(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    event_types: Optional[List[int]] = None,
    owned_only: Optional[bool] = False

) -> List[EventResponse]:
    """
    Get a list of the user's events.

    Args:
        start_time: The start time of the events to get, ISO 8601 strings with timezone (e.g. ...Z). (Optional)
        end_time: The end time of the events to get, ISO 8601 strings with timezone (e.g. ...Z). (Optional)
        event_types: The types of events to get, List[int] (Optional)
        owned_only: Whether to only get events owned by the user, bool (Optional)

    Returns:
        A list of events
        Event Response schema:
            event_id: int
            user_id: int
            event_type: int
            header: Optional[str] = None
            title: str
            start_time: datetime in UTC
            end_time: datetime in UTC
            color: Optional[str] = None
            notes: Optional[str] = None
            series_id: Optional[int] = None
            is_exception: Optional[bool] = False (always false)
            timezone: str = "UTC" (always UTC)
    """

    params = {}
    if start_time:
        params["start_time"] = _iso(_parse_iso(start_time))
    if end_time:
        params["end_time"] = _iso(_parse_iso(end_time))
    if owned_only:
        params["owned_only"] = owned_only
    
    repeated = _as_query_param("event_types[]", event_types)


    async with AsyncClient(base_url=HOURGLASSED_BACKEND_URL, headers=get_auth_header(), timeout=30.0) as client:
        try:
            response = await client.get("/event/", params=[*params.items(), *repeated])
            response.raise_for_status()
            payload = response.json()
            normalized: List[EventResponse] = []
            for item in payload:
                if isinstance(item, dict):
                    if "start_time" in item and isinstance(item["start_time"], str):
                        item["start_time"] = _iso(_parse_iso(item["start_time"]))
                    if "end_time" in item and isinstance(item["end_time"], str):
                        item["end_time"] = _iso(_parse_iso(item["end_time"]))
                normalized.append(EventResponse.model_validate(item))
            return normalized

        except HTTPStatusError as e:
            print(f"Error in getting events: {e}")
            raise



@mcp.tool()
async def get_event(
    event_id: int
) -> EventResponse:
    """
    Get a single event by its id.

    Args:
        event_id: The id of the event to get, int

    Returns:
        An event
        Event Response schema:
            event_id: int
            user_id: int
            event_type: int
            header: Optional[str] = None
            title: str
            start_time: datetime in UTC
            end_time: datetime in UTC
            color: Optional[str] = None
            notes: Optional[str] = None
            series_id: Optional[int] = None
            is_exception: Optional[bool] = False (always false)
            timezone: str = "UTC" (always UTC)
    """

    try:
        async with AsyncClient(base_url=HOURGLASSED_BACKEND_URL, headers=get_auth_header(), timeout=30.0) as client:
            response = await client.get(f"/event/{event_id}")
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                if "start_time" in payload and isinstance(payload["start_time"], str):
                    payload["start_time"] = _iso(_parse_iso(payload["start_time"]))
                if "end_time" in payload and isinstance(payload["end_time"], str):
                    payload["end_time"] = _iso(_parse_iso(payload["end_time"]))
            return EventResponse.model_validate(payload)

    except HTTPStatusError as e:
        print(f"Error in getting event: {e}")
        raise



@mcp.tool()
async def get_series(series_id: int) -> RecurrenceSeriesResponse:
    """
    Get recurrence series by its id.

    Args:
        series_id: The id of the series to get, int

    Returns:
        A recurrence series
        Recurrence Series Response schema:
            series_id: int
            user_id: int
            recurrence_pattern: str (rrule string)
            recurrence_end: datetime in UTC
            created_at: datetime in UTC
    """

    try:
        async with AsyncClient(base_url=HOURGLASSED_BACKEND_URL, headers=get_auth_header(), timeout=30.0) as client:
            response = await client.get(f"/series/{series_id}")
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                if "recurrence_end" in payload and isinstance(payload["recurrence_end"], str):
                    payload["recurrence_end"] = _iso(_parse_iso(payload["recurrence_end"]))
                if "created_at" in payload and isinstance(payload["created_at"], str):
                    payload["created_at"] = _iso(_parse_iso(payload["created_at"]))
            return RecurrenceSeriesResponse.model_validate(payload)
    
    except HTTPStatusError as e:
        print(f"Error in getting series: {e}")
        raise



@mcp.tool()
async def create_event(
    event_type: str,
    title: str,
    start_time: str,
    end_time: str,
    header: Optional[str] = None,
    color: Optional[str] = None,
    notes: Optional[str] = None,
) -> EventResponse:
    """
    Create a new event.

    Args:
        event_type: The type of event to create, str
        title: The title of the event, str
        start_time: The start time of the event, ISO 8601 strings with timezone (e.g. ...Z).
        end_time: The end time of the event, ISO 8601 strings with timezone (e.g. ...Z).
        header: The header of the event, str (Optional)
        color: The color of the event, str (Optional)
        notes: The notes of the event, str (Optional)
    
    Returns:
        The event that was created.
        Event Response schema:
            event_id: int
            user_id: int
            event_type: int
            header: Optional[str] = None
            title: str
            start_time: datetime in UTC
            end_time: datetime in UTC
            color: Optional[str] = None
            notes: Optional[str] = None
            series_id: Optional[int] = None
            is_exception: Optional[bool] = False (always false)
            timezone: str = "UTC" (always UTC)
    """

    body = {
        "event_type": event_type,
        "header": header,
        "title": title,
        "start_time": _iso(_parse_iso(start_time)),
        "end_time": _iso(_parse_iso(end_time)),
        "color": color,
        "notes": notes,
        "timezone": "UTC"
    }
    body = {k: v for k, v in body.items() if v is not None}

    try:
        async with AsyncClient(base_url=HOURGLASSED_BACKEND_URL, headers=get_auth_header(), timeout=30.0) as client:
            response = await client.post("/event/", json=body)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                if "start_time" in payload and isinstance(payload["start_time"], str):
                    payload["start_time"] = _iso(_parse_iso(payload["start_time"]))
                if "end_time" in payload and isinstance(payload["end_time"], str):
                    payload["end_time"] = _iso(_parse_iso(payload["end_time"]))
            return EventResponse.model_validate(payload)

    except HTTPStatusError as e:
        print(f"Error in creating event: {e}")
        raise



@mcp.tool()
async def create_series(
    recurrence_pattern: str,
    event_type: str,
    title: str,
    start_time: str,
    end_time: str,
    recurrence_end: Optional[str] = None,
    header: Optional[str] = None,
    color: Optional[str] = None,
    notes: Optional[str] = None,
)-> RecurrenceSeriesResponse:
    """
    Creating a recurring event.

    Args:
        recurrence_pattern: The recurrence pattern of the event, str
        event_type: The type of event to create, str
        title: The title of the event, str
        start_time: The start time of the event, ISO 8601 strings with timezone (e.g. ...Z).
        end_time: The end time of the event, ISO 8601 strings with timezone (e.g. ...Z).
        recurrence_end: The end time of the recurrence, ISO 8601 strings with timezone (e.g. ...Z). (Optional)
        header: The header of the event, str (Optional)
        color: The color of the event, str (Optional)
        notes: The notes of the event, str (Optional)
    
    Returns:
        The recurrence series that was created.
        Recurrence Series Response schema:
            series_id: int
            user_id: int
            recurrence_pattern: str (rrule string)
            recurrence_end: datetime in UTC
            created_at: datetime in UTC
    """

    body = {
        "recurrence": {
            "recurrence_pattern": recurrence_pattern,
            "recurrence_end": _iso(_parse_iso(recurrence_end)) if recurrence_end else None,
        },
        "event": {
            "event_type": event_type,
            "header": header,
            "title": title,
            "start_time": _iso(_parse_iso(start_time)),
            "end_time": _iso(_parse_iso(end_time)),
            "color": color,
            "notes": notes,
            "timezone": "UTC",
        },
    }
    body["recurrence"] = {k: v for k, v in body["recurrence"].items() if v is not None}
    body["event"] = {k: v for k, v in body["event"].items() if v is not None}

    async with AsyncClient(base_url=HOURGLASSED_BACKEND_URL, headers=get_auth_header(), timeout=30.0) as client:
        try:
            response = await client.post("/series/create", json=body)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                if "recurrence_end" in payload and isinstance(payload["recurrence_end"], str):
                    payload["recurrence_end"] = _iso(_parse_iso(payload["recurrence_end"]))
                if "created_at" in payload and isinstance(payload["created_at"], str):
                    payload["created_at"] = _iso(_parse_iso(payload["created_at"]))
            return RecurrenceSeriesResponse.model_validate(payload)

        except HTTPStatusError as e:
            print(f"Error in creating series: {e}")
            raise





if __name__ == "__main__":
    mcp.run(transport='streamable-http')