import httpx
from .config import AGENT_API_BASE
from .auth import get_headers

async def request_json(method: str, path: str, **kwargs):
    """
    HTTP helper function that merges auth header and surfaces 401 for token refresh
    """
    
    headers = kwargs.pop("headers", {}) | get_headers()
    timeout = httpx.Timeout(20.0, connect=5.0)
    async with httpx.AsyncClient(base_url=AGENT_API_BASE, timeout=timeout) as client:
        response = await client.request(method, path, headers=headers, **kwargs)

        if response.status_code == 401:
            return {"error": "Unauthorized", "status_code": 401, "detail": response.text}

        if response.status_code == 204 or not response.content:
            return {"ok": True}
        
        response.raise_for_status()
        return response.json()
