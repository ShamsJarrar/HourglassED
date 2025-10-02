"""
LLM nodes helper function to call the LLM and
parse the response as a JSON object.

Usage:
    from ._llm import chat_json
    answer = await chat_json(system_prompt, user_input, schema_name="planner_output")
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from typing import Any, Dict, Optional, Sequence
import json
from ..config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL
import traceback

try:
    from openai import AsyncOpenAI
except Exception as e:
    raise RuntimeError(
        "OpenAI is not installed. Please install it with 'pip install openai'."
        ) from e


llm = ChatOpenAI(
    api_key=OPENROUTER_API_KEY, 
    model="gpt-4o-mini",
    base_url=OPENROUTER_BASE_URL
).bind(response_format={"type": "json_object"})


async def chat_json(
    system_prompt: str, 
    user_input: str, 
    schema_name: str = "json_object", 
    history: Optional[Sequence[BaseMessage]] = None
) -> Dict[str, Any]:
    """
    Call the LLM with system+user prompts and ask for strict JSON output.

    Returns:
        Python dict (empty dict if failed)
    """
    
    try:
        messages = list(history or [])
        messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_input))
        response = await llm.ainvoke(messages)
        return json.loads(response.content)
    
    except Exception as e:
        traceback.print_exc()
        print("LLM ERROR:", repr(e))
        return {}
