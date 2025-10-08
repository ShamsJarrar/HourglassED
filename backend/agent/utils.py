from langchain_core.messages import ToolMessage
from datetime import datetime, timezone
from typing import Union, Any, Tuple
import json

def _get_text_from_tool_message(message: ToolMessage) -> str:
    if isinstance(message.content, str):
        return message.content
    if isinstance(message.content, list):
        for p in message.content:
            if isinstance(p, dict) and p.get("type") == "text" and "text" in p:
                return p["text"]
    return ""


def _iso(date: Any) -> Union[str, None]:
    if date is None:
        return None
    if isinstance(date, datetime):
        return date.isoformat()
    return str(date)


def _normalize_tool_result(result: Any) -> Tuple[str, Any]:
    """
    Returns (content_string, parsed_object_for_schema_validation)
    """

    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            parsed = None
        return result, parsed

    # if not a string
    return json.dumps(result), result