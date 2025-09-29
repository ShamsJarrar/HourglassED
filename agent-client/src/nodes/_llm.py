"""
LLM nodes helper function to call the LLM and
parse the response as a JSON object.

Usage:
    from ._llm import chat_json
    answer = await chat_json(system_prompt, user_input, schema_name="planner_output")
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Any, Dict
import json
from ..config import OPENROUTER_API_KEY

try:
    from openai import AsyncOpenAI
except Exception as e:
    raise RuntimeError(
        "OpenAI is not installed. Please install it with 'pip install openai'."
        ) from e


llm = ChatOpenAI(
    api_key=OPENROUTER_API_KEY, 
    model="gpt-4o-mini",
    temperature=0.1,
)


async def chat_json(system_prompt: str, user_input: str, schema_name: str = "json_object") -> Dict[str, Any]:
    """
    Call the LLM with system+user prompts and ask for strict JSON output.

    Returns:
        Python dict (empty dict if failed)
    """
    
    try:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_input)]
        response = await llm.ainvoke(messages)
        return json.loads(response.content)
    
    except Exception as e:
        return {}
