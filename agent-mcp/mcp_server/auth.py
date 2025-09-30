from typing import Optional


API_TOKEN: Optional[str] = None

def get_headers() -> dict:
    return {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}

def register_auth(mcp):
    @mcp.tool("auth.set_token")
    async def set_token(auth_token: str):
        """
        Set API token for agent use
        """
        global API_TOKEN
        API_TOKEN = auth_token
        return {"ok": True}