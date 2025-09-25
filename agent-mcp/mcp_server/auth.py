from fastmcp import tool


API_TOKEN: str | None = None

def get_headers() -> dict:
    return {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}

@tool("auth.set_token", desc= "Set API token for agent use")
async def set_token(auth_token: str):
    global API_TOKEN
    API_TOKEN = auth_token
    return {"ok": True}