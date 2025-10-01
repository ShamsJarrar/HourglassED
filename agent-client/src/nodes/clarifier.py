"""
Clarifier node: given the current slots + prefs + user input, ask the user for clarification
using only blocking questions that are needed to proceed.
- Merges any inferred/confirmed value into state.slots.
- Set state.needs_clarification accordingly.
- Optionally place a short question/answer into state.answer foe UI.

Inputs:
    state.user_text (str)
    state.slots (Slots)
    state.prefs (Prefs)
    state.intent (Literal["ask","add","plan","other"])

Outputs:
    state.slots (merged)
    state.needs_clarification (bool)
    state.answer (short question/message to present)
"""
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import interrupt
from typing import Any, Dict, List
from ..state import AgentState, Slots, Prefs
from ._llm import chat_json


CLARIFIER_PROMPT = """
Ypu are the Clarifier for a student-oriented calender agent.
Ask ONLY the minimal, blocking questions that are needed to proceed with the user's intent.

You are given the user's request, the slots that have been inferred, and the name of
the fields that are missing.
You should ask for the most critical missing field (like time, date, etc)
Be specific and concise (max ~20 words). Do NOT answer the original request.

Return STRICT JSON:
{
    "question": str     // the question to ask the user
}

"""


async def clarifier(state: AgentState, config=None) -> AgentState:
    intent = (state.get("intent") or "").lower()
    user_q = state.get("user_input") or ""
    slots: Slots = state.get("slots") or {}
    missing_fields: List[str] = state.get("missing_fields")

    response = await chat_json(
        system_prompt=CLARIFIER_PROMPT,
        user_input=f"User asked: {user_q}\n slots: {slots}\n missing_fields: {missing_fields}",
        history=state.get("messages", [])
    )
    msgs = list(state.get("messages", []))
    msgs.append(AIMessage(content=str(response), name="clarifier"))
    state["messages"] = msgs
    
    question = (response or {}).get("question") if isinstance(response, dict) else None
    user_reply: str = interrupt(question)


    msgs = list(state.get("messages", []))
    msgs.append(HumanMessage(content=user_reply))
    state["messages"] = msgs

    missing_fields = []

    return state