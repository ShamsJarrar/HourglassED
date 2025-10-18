#!/bin/bash
echo "🚀 Launching full HourglassED stack..."

# In Git Bash terminal run before chmod +x scripts/*.sh
# Make sure docker is opened before running this script

SCRIPT_DIR="$(dirname "$0")"

start "" "C:\Program Files\Git\bin\bash.exe" -lc "\"$SCRIPT_DIR/start_mcp.sh\"; exec bash"
start "" "C:\Program Files\Git\bin\bash.exe" -lc "\"$SCRIPT_DIR/start_celery.sh\"; exec bash"
start "" "C:\Program Files\Git\bin\bash.exe" -lc "\"$SCRIPT_DIR/start_backend.sh\"; exec bash"
start "" "C:\Program Files\Git\bin\bash.exe" -lc "\"$SCRIPT_DIR/start_frontend.sh\"; exec bash"

echo "✅ All services launched!"