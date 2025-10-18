#!/bin/bash
set -euo pipefail

# Open Docker before running this script

echo "🧱 Starting Redis container..."
docker start redis >/dev/null 2>&1 || docker run -d -p 6379:6379 --name redis redis

echo "🐍 Starting Celery worker and beat..."

SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
BACKEND_DIR="$SCRIPT_DIR/../backend"
BACKEND_WIN_PATH="$(cygpath -w "$BACKEND_DIR")"

cd "$(dirname "$0")/../backend"
source venv/Scripts/activate
python -m celery -A tasks worker --loglevel=info --pool=solo &
sleep 1
python -m celery -A tasks beat --loglevel=info &
wait

echo "✅ Celery worker and beat started."