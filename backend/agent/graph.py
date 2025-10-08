from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, ToolMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from .state import AgentState, OrganizerReply, createSeriesWithEvents
from .utils import _get_text_from_tool_message, _iso, _normalize_tool_result
from schemas.event import EventResponse
from schemas.recurrence_series import RecurrenceSeriesResponse
from dotenv import load_dotenv
from typing import List, Union
from pydantic import ValidationError
import os
import json



# Environment Variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MCP_URL = os.getenv("MCP_URL")
DATABASE_URL = os.getenv("DATABASE_URL")



# MCP Client Set Up
client = MultiServerMCPClient(
    {
        "hourglassed-calendar-mcp": {
            "url": MCP_URL,
            "transport": "streamable-http"
        }
    }
)
tools = client.get_tools()
tools_name = {t.name: t for t in tools}



# Model Set Up
base_model = ChatOpenAI(
    api_key=OPENROUTER_API_KEY,
    model="gpt-4o-mini",
    base_url=OPENROUTER_BASE_URL
).bind_tools(tools)

model = base_model.with_structured_output(OrganizerReply)



# Nodes Definition
async def set_access_token(state: AgentState) -> AgentState:
    token = state.get("access_token")
    if not token:
        return {}
    

    response = await tools_name["pass_access_token"].ainvoke({'access_token': token})
    tool_message = ToolMessage(
        name="pass_access_token",
        content=str(response),
        tool_call_id=f"manual#pass_access_token"
    )

    return {'messages': [tool_message]}


async def organizer(state: AgentState) -> AgentState:
    user_input = state['user_input']
    user_feedback = state.get("user_feedback")
    answer = state.get("answer")
    calendar = state.get("calendar", [])
    max_tool_calls = state.get("max_tool_calls", 4)
    status = state.get("status", "approved")
    proposed_events = state.get("proposed_events", [])


    initial_system_prompt = SystemMessage(content=f"""
    You are an organizer assistant for a student-oriented calendar app. Your job is to help the user
    organize their schedule based on their input.

    Use ONLY the read-only tools:
    - get_events
    - get_event
    - get_series

    You may call tools up to {max_tool_calls} times.

    Times must be ISO 8601 with offset or Z (e.g., 2025-10-06T09:00:00-04:00 or 2025-10-06T13:00:00Z).
    Use the timezone of the user's current location.

    If an event has a series_id, fetch the series to see recurrence details.

    After fetching what you need, return JSON in this exact shape:
    {{
    "answer": "your response here",
    "proposed_events": [
        /* zero or more EventCreate or CreateSeriesWithEvents objects */
    ]
    }}

    Event proposal schema:
    {{
    "event_type": "str",
    "header": "str | null",
    "title": "str",
    "start_time": "datetime string",
    "end_time": "datetime string",
    "color": "str | null",
    "notes": "str | null"
    }}

    Recurring proposal schema:
    {{
    "recurrence": {{
        "recurrence_pattern": "str",
        "recurrence_end": "datetime string"
    }},
    "event": <event schema above>
    }}

    Current calendar snapshot (read-only): {calendar}
    """)

    feedback_system_prompt = SystemMessage(content=f"""
    You are an organizer assistant. Update your prior response based on the user's feedback.
    Address all comments, corrections, or suggestions provided by the human

    Previous answer: {answer}
    Previous proposed_events: {proposed_events}
    User feedback: {user_feedback}
    Current read-only calendar snapshot: {calendar}

    If you need more information, you can call the tools again.
    You can only call the tools upto {max_tool_calls} times.
    Use ONLY the read-only tools:
    - get_events
    - get_event
    - get_series

    Times must be ISO 8601 with offset or Z (e.g., 2025-10-06T09:00:00-04:00 or 2025-10-06T13:00:00Z).
    Use the timezone of the user's current location.

    If an event has a series_id, fetch the series to see recurrence details.

    Return JSON ONLY in the same schema:
    {{
    "answer": "your revised response here",
    "proposed_events": [ /* updated proposals or [] */ ]
    }}
    """)


    if status == "feedback" and user_feedback:
        messages = List[BaseMessage] = [
            feedback_system_prompt,
            *state["messages"],
            HumanMessage(content=user_feedback),
        ]
    
    else:
        messages = [
            initial_system_prompt,
            HumanMessage(content=user_input)
        ]

    response: OrganizerReply = await model.ainvoke(messages)

    ai_message = AIMessage(content = json.dumps(response.model_dump(mode="json")))
    
    return {
        "messages": messages + [ai_message],
        "answer": response.answer,
        "proposed_events": response.proposed_events
    }
        

tools_node = ToolNode(tools)


async def save_tool_results(state: AgentState) -> AgentState:
    tool_messages = [message for message in state['messages'] if isinstance(message, ToolMessage)]
    if not tool_messages:
        return {}
    
    last_tool_message = tool_messages[-1]
    raw_tool_result = _get_text_from_tool_message(last_tool_message)

    try:
        data = json.loads(raw_tool_result) if raw_tool_result else None
    except json.JSONDecodeError:
        return {}
    
    tool_name = (last_tool_message.name).strip()

    if tool_name == "get_events" and isinstance(data, list):
        items = [EventResponse.model_validate(x) for x in data]
        return {"calendar": items}
    
    if tool_name == "get_event" and isinstance(data, dict):
        return {"calendar": [EventResponse.model_validate(data)]}
    
    if tool_name == "get_series" and isinstance(data, dict):
        return {"calendar": [RecurrenceSeriesResponse.model_validate(data)]}
    
    return {}


async def human_feedback(state: AgentState):
    pass


async def commit_proposed_events(state: AgentState) -> AgentState:
    proposals = state.get('proposed_events') or []
    if not proposals or proposals == []:
        return {}
    
    tool_messages: List[ToolMessage] = []
    calendar_updates: List[Union[EventResponse, RecurrenceSeriesResponse]] = []

    for idx, item in enumerate(proposals):
        is_series = False
        recurrence = None
        event = None

        if isinstance(item, createSeriesWithEvents) or (isinstance(item, dict) and "recurrence" in item and "event" in item):
            is_series = True
            data = item.model_dump() if hasattr(item, "model_dump") else item
            recurrence = data["recurrence"]
            event = data["event"]
        
        else:
            data = item.model_dump() if hasattr(item, "model_dump") else item
            event = data["event"]
        
        if is_series:
            args = {
                "recurrence_pattern": recurrence.get("recurrence_pattern"),
                "event_type": event.get("event_type"),
                "title": event.get("title"),
                "start_time": _iso(event.get("start_time")),
                "end_time": _iso(event.get("end_time")),
                "recurrence_end": _iso(recurrence.get("recurrence_end")),
                "header": event.get("header"),
                "color": event.get("color"),
                "notes": event.get("notes"),
            }
            args = {k: v for k, v in args.items() if v is not None}

            response = await tools_name["create_series"].ainvoke(args)
            content_string, parsed_object = _normalize_tool_result(response)

            tool_messages.append(
                ToolMessage(
                    name="create_series",
                    content=content_string,
                    tool_call_id=f"manual#create_series#{idx}"
                )
            )

            if parsed_object:
                try:
                    series = RecurrenceSeriesResponse.model_validate(parsed_object)
                    calendar_updates.append(series)
                except ValidationError:
                    pass
        
        else:
            args = {
                "event_type": event.get("event_type"),
                "title": event.get("title"),
                "start_time": _iso(event.get("start_time")),
                "end_time": _iso(event.get("end_time")),
                "header": event.get("header"),
                "color": event.get("color"),
                "notes": event.get("notes"),
            }
            args = {k: v for k, v in args.items() if v is not None}

            response = await tools_name["create_event"].ainvoke(args)
            content_string, parsed_object = _normalize_tool_result(response)

            tool_messages.append(
                ToolMessage(
                    name="create_event",
                    content=content_string,
                    tool_call_id=f"manual#create_event#{idx}"
                )
            )

            if parsed_object:
                try:
                    event = EventResponse.model_validate(parsed_object)
                    calendar_updates.append(event)
                except ValidationError:
                    pass
    
    return {
        "messages": tool_messages,
        "calendar": calendar_updates,
        "proposed_events": [],
        "answer": "Committed proposed events"
    }



# Routers definition
def after_organizer(state: AgentState):
    last_message = state['messages'][-1]

    if not last_message.tool_calls:
        return 'human_feedback'
    else:
        return 'tools'


def after_human_interrupt(state: AgentState):
    current_state = state['state']

    if current_state == "approved":
        return 'commit_proposed_events'
    elif current_state == "feedback":
        return 'organizer'
    else:
        return END



# Graph Construction
graph = StateGraph(AgentState)

graph.add_node("set_access_token", set_access_token)
graph.add_node("organizer", organizer)
graph.add_node("tools", tools_node)
graph.add_node("save_tool_results", save_tool_results)
graph.add_node("human_feedback", human_feedback)
graph.add_node("commit_proposed_events", commit_proposed_events)

graph.add_edge(START, "set_access_token")
graph.add_edge("set_access_token", "organizer")

graph.add_conditional_edges(
    "organizer",
    after_organizer,
    {
        'tools': 'tools',
        'human_feedback': 'human_feedback'
    }
)

graph.add_edge("tools", "save_tool_results")
graph.add_edge("save_tool_results", "organizer")

graph.add_conditional_edges(
    'human_feedback',
    after_human_interrupt,
    {
        'approved': 'commit_proposed_events',
        'feedback': 'organizer',
        'skip': END
    }
)

graph.add_edge("commit_proposed_events", END)
