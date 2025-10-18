#!/bin/bash
echo "🚀 Starting MCP server..."

cd "$(dirname "$0")/../hourglassed-mcp" || exit
source .mcpenv/Scripts/activate
python server.py