from fastmcp import FastMCP
from mcp_server.tools import *
from mcp_server.auth import set_token


mcp = FastMCP("hourglassed-agent-mcp", host="127.0.0.1", port=8765)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")