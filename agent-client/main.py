from langchain_core.messages import HumanMessage, AIMessage
from src.build_graph import build_graph
from src.mcp_tools import MCPTools
from src.state import initial_state
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import json
import asyncio
import os


TOOLS: MCPTools | None = None


async def _init_mcp_and_set_token(token: Optional[str]) -> None:
    """
    Initialize the MCP server and optionally set the token.

    Notes:
    - In production, the frontend will call /token
    - In development, the token is set here from .env, where it calls 'auth.set_token' tool
    """

    global TOOLS
    if TOOLS is None:
        TOOLS = MCPTools()
        await TOOLS.init_session()


    if token:
        try:
            await TOOLS.call("auth.set_token", {"auth_token": token})
            print("MCP token set")
        except Exception as e:
            print(f"Error setting MCP token: {e}")


def _compile_graph():
    return build_graph()


async def _run_turn(
    app, 
    user_input: str,
    prev_state: Optional[Dict[str, Any]] = None,
    dump_state: bool = False
) -> Dict[str, Any]:
    """
    Run the LangGraph agent once:
    - Build state from user input and seed
    - Invoke the compiled graph
    - Print either state['answer'] or full state if dump_state is True
    - return state
    """

    if not prev_state:
        state_input = initial_state(user_input)  
        state_input["messages"] = [HumanMessage(content=user_input)]
    else:
        state_input = dict(prev_state)
        state_input["user_input"] = user_input
        state_input["messages"] = [HumanMessage(content=user_input)]


    config = {"configurable": {"tools": TOOLS}}
    if hasattr(app, "ainvoke"):
        response = await app.ainvoke(state_input, config=config)
    elif hasattr(app, "invoke"):
        response = await app.invoke(state_input, config=config)
    else:
        raise RuntimeError("App does not have an invoke method")
    

    answer = response.get("answer")

    
    if dump_state:
        print(json.dumps(response, indent=2, default=str))
    else:
        answer = response.get("answer")
        print(answer if answer else json.dumps(response, indent=2, default=str))
    
    return response
    
    

# ---------------------------- CLI MODE ----------------------------
def main_cli():
    """
    Dev REPL:
    - Type user message to run a turn
    - Prints 'answer' or full state of dump_state = True
    - '/token <jwt>' to set/replace token
    - '/exit' to exit
    """

    print("***********Agent REPL***********")
    print("**Loading .env and compiling graph...")
    load_dotenv()

    start_token = os.getenv("TEMP_USER_ACCESS_TOKEN")

    asyncio.run(_init_mcp_and_set_token(start_token))

    app = _compile_graph()
    dump_state = True

    print("**Ready. Type '/token <jwt>' to set/replace token or '/exit' to exit \n")

    try:
        running_state = None
        while True:
            try:
                user_input = input("you>>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break
            
            if not user_input:
                continue
            if user_input.lower() in ('/exit', 'exit', 'quit', '/quit', 'q'):
                print("\nBye!")
                break
            
            if user_input.startswith('/token'):
                token = user_input.split(" ", 1)[1].strip()
                try:
                    asyncio.run(_init_mcp_and_set_token(token))
                    print("MCP token updated")
                except Exception as e:
                    print(f"Error setting MCP token: {e}")
                continue
            

            try:
                response = asyncio.run(_run_turn(app, user_input, prev_state=running_state, dump_state=dump_state))
                running_state = response
            except Exception as e:
                print(f"Error running turn: {e}")
                continue

    finally:
        if TOOLS is not None:
            asyncio.run(TOOLS.aclose())



# ---------------------------- HTTP server mode for frontend ----------------------------
class TurnInput(BaseModel):
    user_input: str = Field(..., description="User message for this turn")
    state: Optional[Dict[str, Any]] = Field(None, description="Prior agent state (if any)")
    dump_state: bool = Field(False, description="Return full state for debugging")

class TokenInput(BaseModel):
    token: str = Field(..., description="JWT to forward to MCP server via auth.set_token")


_compiled_graph = None

@asynccontextmanager
async def lifespan(app):
    load_dotenv()
    global _compiled_graph
    _compiled_graph = _compile_graph()

    # dev only: set token from .env
    token = os.getenv("TEMP_USER_ACCESS_TOKEN")
    await _init_mcp_and_set_token(token)

    try:
        yield
    finally:
        if TOOLS is not None:
            asyncio.run(TOOLS.aclose())



app_http = FastAPI(title="HourglassED Agent", lifespan=lifespan)
    

@app_http.get('/health')
async def health():
    graph_ok = _compiled_graph is not None
    mcp_ok = TOOLS is not None
    return {"ok": graph_ok and mcp_ok, "graph": graph_ok, "mcp": mcp_ok}


@app_http.post('/token')
async def http_set_token(payload: TokenInput):
    """
    Frontend calls this endpoints after login to forward the user's JWT.
    stored inside the MCP server (auth.set_token) to access backend APIs.
    """
    try:
        await _init_mcp_and_set_token(payload.token)        # reuses TOOLS
    except Exception as e:
        return {'error': str(e)}
    
    return {'ok': True}


@app_http.post('/turn')
async def http_turn(payload: TurnInput):
    """
    Run one turn of the agent and return the new state.
    """

    if _compiled_graph is None:
        return {'error': 'Graph not initialized'}
    
    try:
        response = await _run_turn(
            _compiled_graph,
            payload.user_input,
            prev_state=payload.state,
            dump_state=payload.dump_state
        )
        return response
    except Exception as e:
        return {'error': str(e)}



# ---------------------------- Uvicorn entry point ----------------------------
if __name__ == "__main__":
    
    # Mode: CLI (0) or HTTP (1)
    if os.getenv("OPERATING_MODE", "0") == "1":
        import uvicorn
        host = os.getenv("AGENT_HOST", "127.0.0.1")
        port = int(os.getenv("AGENT_PORT", "5057"))
        uvicorn.run("main:app_http", host=host, port=port, reload=False)
    else:
        main_cli()
