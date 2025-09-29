from langgraph.graph import StateGraph, START, END
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


# ROUTERS
def _needs_clarification(state: AgentState) -> str:
    """
    After planner:
        if needs_clarification is True route to 'clarifier' 
        else route to 'prefs'
    """

    return "clarifier" if state["needs_clarification"] else "prefs"


def _clarifier_next(state: AgentState) -> str:
    """
    After clarifier:
        if information is still missing, END so UI can ask for missing info.
        else proceed to 'prefs'
    """
    return END if state["needs_clarification"] else "prefs"



# GRAPH BUILDING
def build_graph():
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("planner", planner)
    graph.add_node("clarifier", clarifier)
    graph.add_node("prefs", ensure_prefs)
    graph.add_node("tools", read_calendar)
    graph.add_node("organizer", organizer)
    graph.add_node("reviewer", reviewer)
    graph.add_node("proposer", proposer)
    graph.add_node("presenter", presenter)

    # Edges
    graph.add_edge(START, "planner")

    graph.add_conditional_edges(
        "planner",
        _needs_clarification,
        {
            'clarifier': 'clarifier',
            'prefs': 'prefs'
        }
    )

    graph.add_conditional_edges(
        'clarifier',
        _clarifier_next,
        {
            END: END,
            'prefs': 'prefs'
        }
    )

    graph.add_edge('prefs', 'tools')
    graph.add_edge('tools', 'organizer')
    graph.add_edge('organizer', 'reviewer')
    graph.add_edge('reviewer', 'proposer')
    graph.add_edge('proposer', 'presenter')
    graph.add_edge('presenter', END)

    
    return graph.compile()
