# since the mcp server is running over streamable-http,
# and requires post request to access tools,
# this file is a simple wrapper to not duplicate code in every node
# and acts as an adapter between the client and server

from fastmcp.client import Client
from .config import MCP_URL, TEMP_USER_ACCESS_TOKEN
from typing import Optional, Any, Dict


class MCPError(RuntimeError):
    """Exception raised when an MCP server return an error"""


class MCPTools:
    """ 
    HTTP client for MCP server

    Usage:
        tools = MCPTools()
        await tools.init_session()      # dev-tool
        await tools.set_token("<jwt>")  
        response = await tools.call("tool.name", {...})
    """

    def __init__(self, base_url: str = MCP_URL, access_token: Optional[str] = TEMP_USER_ACCESS_TOKEN):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token or ""        # dev only, token is injected to MCP via auth.set_token to be used by the backend
        self._client: Optional[Client] = None

    
    async def _ensure_client(self) -> Client:
        if self._client is None:
            self._client = Client(self.base_url)
            await self._client.__aenter__()
        return self._client


    async def call(self, tool_name: str, args: Dict[str, Any]) -> Any:
        client = await self._ensure_client()
        try:
            result = await client.call_tool(tool_name, args or {})
            return getattr(result, 'data', result)
        except Exception as e:
            raise MCPError(str(e))
    

    async def set_token(self, token: str) -> Any:
        """
        To forward frontend access token to MCP.
        """
        self.access_token = token
        return await self.call("auth.set_token", {"auth_token": token})


    async def init_session(self) -> Any:
        """
        Dev tool to push access token from .env at startup.
        """

        if self.access_token:
            await self.set_token(self.access_token)
    

    async def aclose(self):
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None
