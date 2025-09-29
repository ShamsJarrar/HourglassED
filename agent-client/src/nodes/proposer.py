"""
Proposer node:
- Convert normalized drafts into pending proposals (no calendar writes)
- Calls MCP propose tools:
    - agent.propose_create_event
    - agent.propose_update_event
    - agent.propose_delete_event
- Returns AgentProposalResponse

Inputs in state:
    drafts: List[Draft]        # from organizer/reviewer nodes
    review: Review             # optional, used to craft reasoning_summary
    prefs: Prefs               # optional
    slots: Slots               # optional
    intent: str                # for summary context

Outputs in state:
    proposals: { "items": [ ...AgentProposalResponse... ] }
    pending_proposal_id: Optional[int]   # set when exactly one proposal created
    answer: Optional[str]                # may keep or append a short status
"""


from typing import Any, Dict, List, Optional
import json
from ..state import AgentState, Draft, Proposals
from ..mcp_tools import MCPTools, MCPError


tools = MCPTools()


def _reasoning_summary(state: AgentState) -> str:
    """
    Build short reasoning_summary (max. 255 chars)
    """
    intent = state.get("intent", "")
    slots = state.get("slots", {}) or {}
    title = slots.get("title") or ""
    review = state.get("review") or {}
    suggs = review.get("suggestions") or []
    issues = review.get("issues") or []
    score = review.get("score")

    parts: List[str] = []
    if intent:
        parts.append(f"intent={intent}")
    if title:
        parts.append(f"title={title}")
    if isinstance(score, (int, float)):
        parts.append(f"score={score}")
    if suggs:
        parts.append(" ".join(suggs[:2]))
    elif issues:
        parts.append(" ".join(issues[:2]))

    summary = " | ".join([p for p in parts if p]) or "calendar plan proposal"
    return summary[:255]



async def _propose_event(draft: Draft, reasoning_summary: str) -> Dict[str, Any]:
    """
    Send a single draft to the right propose_* tool
    Returns proposel object or error dict
    """
    action = (draft.get("action") or "").lower()
    body = draft.get("body") or {}
    payload = {
        "draft": draft,
        "reasoning_summary": reasoning_summary
    }

    try:
        if action == "create":
            response = await tools.call("agent.propose_create_event", {
                "draft_json": json.dumps(payload)
            })
            return {"ok": True, "proposal": response}
        
        elif action == "update":
            response = await tools.call("agent.propose_update_event", {
                "draft_json": json.dumps(payload)
            })
            return {"ok": True, "proposal": response}
        
        elif action == "delete":
            response = await tools.call("agent.propose_delete_event", {
                "draft_json": json.dumps(payload)
            })
            return {"ok": True, "proposal": response}
        
        else:
            return {"ok": False, "error": f"Unknown action: {action}"}
    
    except MCPError as e:
        return {"ok": False, "error": f"MCP error: {str(e)}"}
    
    except Exception as e:
        return {"ok": False, "error": f"Exception: {str(e)}"}



async def proposer(state: AgentState) -> AgentState:
    drafts: List[Draft] = list(state.get("drafts") or [])
    if not drafts:
        state["proposals"] = Proposals(items=[])
        state["pending_proposal_id"] = None
        state["answer"] = state.get("answer") or "No drafts generated to propose"
        return state
    
    reasoning_summary = _reasoning_summary(state)

    proposals: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for d in drafts:
        response = await _propose_event(d, reasoning_summary)
        if response.get("ok"):
            proposal = response.get("proposal") or {}
            proposals.append(proposal)
        else:
            errors.append({"draft": d, "error": response.get("error")})
    
    state["proposals"] = Proposals(items=proposals)

    if len(proposals) == 1:
        pending_proposal_id = proposals[0].get("event_id")
        state["pending_proposal_id"] = pending_proposal_id if isinstance(pending_proposal_id, int) else None
    else:
        state["pending_proposal_id"] = None


    num_proposals = len(proposals)
    failed_proposals = len(errors)
    message = f"{num_proposals} proposals created, {failed_proposals} failed."

    if failed_proposals:
        state["propose_errors"] = errors
    
    if not state.get("answer"):
        state["answer"] = message
    
    return state

