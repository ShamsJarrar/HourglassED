from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableLambda
from .state import AgentState
from .nodes.planner import planner
from .nodes.clarifier import clarifier
from .nodes.prefs import ensure_prefs
from .nodes.tools import read_calendar
from .nodes.organizer import organizer
from .nodes.reviewer import reviewer
from .nodes.proposer import proposer
from .nodes.presenter import presenter
from typing import Any


REVIEW_SCORE_THRESHOLD = 0.6
REVIEW_COUNT_THRESHOLD = 3


# ROUTERS
def router_after_planner(state: AgentState) -> str:
    if state["needs_clarification"]:
        return "clarifier"
    intent = (state.get("intent") or "other").lower()
    return "tools" if intent in ["ask", "other"] else "prefs"


def router_after_tools(state: AgentState) -> str:
    return "presenter" if (state.get("intent") or "").lower() in ["ask", "other"] else "organizer"


def router_after_reviewer(state: AgentState) -> str:
    review = state.get("review") or {}
    score = float(review.get("score", 1.0))
    return "organizer" if (score < REVIEW_SCORE_THRESHOLD and state.get("review_count", 3) < REVIEW_COUNT_THRESHOLD) else "proposer"



# GRAPH BUILDING
def build_graph():
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("planner", RunnableLambda(planner))
    graph.add_node("clarifier", RunnableLambda(clarifier))
    graph.add_node("prefs", RunnableLambda(ensure_prefs))
    graph.add_node("tools", RunnableLambda(read_calendar))
    graph.add_node("organizer", RunnableLambda(organizer))
    graph.add_node("reviewer", RunnableLambda(reviewer))
    graph.add_node("proposer", RunnableLambda(proposer))
    graph.add_node("presenter", RunnableLambda(presenter))

    # Edges
    graph.add_edge(START, "planner")

    graph.add_conditional_edges(
        "planner",
        router_after_planner,
        {
            "clarifier": "clarifier",
            "tools": "tools",
            "prefs": "prefs"
        }
    )

    graph.add_edge("clarifier", "planner")
    graph.add_edge("prefs", "tools")

    graph.add_conditional_edges(
        "tools",
        router_after_tools,
        {
            "presenter": "presenter",
            "organizer": "organizer"
        }
    )

    graph.add_edge("organizer", "reviewer")

    graph.add_conditional_edges(
        "reviewer",
        router_after_reviewer,
        {
            "organizer": "organizer",
            "proposer": "proposer"
        }
    )

    graph.add_edge("proposer", "presenter")
    graph.add_edge("presenter", END)

    
    return graph.compile()
