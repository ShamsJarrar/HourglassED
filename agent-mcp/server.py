from fastmcp import FastMCP
from mcp_server import register_all


mcp = FastMCP("hourglassed-agent-mcp", host="127.0.0.1", port=8765)
register_all(mcp)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")