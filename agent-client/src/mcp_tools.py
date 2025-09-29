# since the mcp server is running over streamable-http,
# and requires post request to access tools,
# this file is a simple wrapper to not duplicate code in every node
# and acts as an adapter between the client and server

from .config import MCP_URL, TEMP_USER_ACCESS_TOKEN
from typing import Optional, Any, Dict
import httpx


class MCPError(RuntimeError):
    """Exception raised when an MCP server return an error"""


class MCPTools:
    """ 
    HTTP client for MCP server

    Usage:
        tools = MCPTools()
        await tools.init_session()      # dev-tool
        await tools.set_token("<jwt>")  
        response = await tools.call("agent.get_prefs", {})
    """

    def __init__(self, base_url: str = MCP_URL, access_token: Optional[str] = TEMP_USER_ACCESS_TOKEN):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token        # dev only, token is injected to MCP via auth.set_token to be used by the backend

    
    async def _post(self, path: str, json: Dict[str, Any]) -> Any:
        url = f"{self.base_url}{path}"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
            response = await client.post(url, json=json)

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                detail = None
                try:
                    detail = response.json()
                except Exception:
                    detail = response.text
                raise MCPError(f"MCP HTTP {response.status_code}: {detail} at {url}:{detail}")
            
            try:
                return response.json()
            except ValueError:
                return {}
    

    async def call(self, tool_name: str, args: Dict[str, Any]) -> Any:
        payload = {"name": tool_name, "arguments": args}
        return await self._post("/tools/call", payload)
    

    async def set_token(self, token: str) -> Any:
        """
        To forward frontend access token to MCP.
        """
        self.access_token = token
        return await self.call("auth.set_token", {"access_token": token})


    async def init_session(self) -> Any:
        """
        Dev tool to push access token from .env at startup.
        """

        if self.access_token:
            await self.set_token(self.access_token)
