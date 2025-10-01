from dotenv import load_dotenv
import os

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8765/mcp").rstrip("/")
AGENT_HOST=os.getenv("AGENT_HOST", "127.0.0.1")
AGENT_PORT=os.getenv("AGENT_PORT", "5057")
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")
DEFAULT_LIST_WINDOWS = int(os.getenv("DEFAULT_LIST_WINDOWS", "14"))
TEMP_USER_ACCESS_TOKEN = os.getenv("TEMP_USER_ACCESS_TOKEN", "")
OPERATING_MODE = os.getenv("OPERATING_MODE", "0")


if OPENROUTER_API_KEY == "":
    raise RuntimeError("LLM API key needs to be set!")

