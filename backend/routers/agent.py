from fastapi import APIRouter, Depends, Request, HTTPException
from uuid import uuid4
from dependencies import get_db, get_current_user
from sqlalchemy.orm import Session
from schemas.agent import InitialRequest, ResumeRequest, AgentResponse
from models.user import User


router = APIRouter(prefix='/agent', tags=['Agent'])


async def run_graph(graph, input_state: dict, config) -> AgentResponse:
    response = await graph.ainvoke(input_state, config=config)
    state = await graph.aget_state(config)
    next_nodes = state.next or []
    run_state = "user_feedback" if "human_feedback" in next_nodes else "finished"
    thread_id = config['configurable']['thread_id']

    return AgentResponse(
        thread_id=thread_id,
        run_state=run_state,
        answer=response.get('answer', ''),
        proposed_events=response.get('proposed_events', [])
    )


@router.post('/start', response_model=AgentResponse)
async def start(
    initial_request: InitialRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    graph = request.app.state.graph
    if graph is None:
        raise HTTPException(status_code=500, detail="Graph not found")
    
    thread_id = str(uuid4())
    config = {'configurable': {'thread_id': thread_id}}

    auth = request.headers.get('Authorization', '')
    token = auth.split(" ", 1)[1] if auth.lower().startswith("bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    
    initial_state = {
        "messages": [],
        "user_input": initial_request.user_input,          
        "user_feedback": None,
        "proposed_events": [],
        "answer": "",
        "calendar": [],
        "max_tool_calls": initial_request.max_tool_calls if hasattr(initial_request, "max_tool_calls") else 4,
        "status": "approved",
        "access_token": token,
    }
    

    return await run_graph(graph, initial_state, config)


@router.post('/resume', response_model=AgentResponse)
async def resume(
    resume_request: ResumeRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    graph = request.app.state.graph
    if graph is None:
        raise HTTPException(status_code=500, detail="Graph not found")
    
    config = {'configurable': {'thread_id': resume_request.thread_id}}

    state_update = {'status': resume_request.status}
    if resume_request.user_feedback is not None:
        state_update['user_feedback'] = resume_request.user_feedback

    await graph.aupdate_state(config, state_update)

    return await run_graph(graph, {}, config)

