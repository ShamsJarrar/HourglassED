from .auth import register_auth
from .tools import register_tools

def register_all(mcp):
    register_tools(mcp)
    register_auth(mcp)
