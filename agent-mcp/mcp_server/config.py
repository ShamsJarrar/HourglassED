import os
from dotenv import load_dotenv

load_dotenv()
AGENT_API_BASE = os.getenv("AGENT_API_BASE", "http://127.0.0.1:8000")
DEFAULT_LIST_WINDOW_DAYS = int(os.getenv("DEFAULT_LIST_WINDOW_DAYS", "14"))
