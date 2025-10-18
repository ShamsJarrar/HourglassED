#!/bin/bash
echo "⚙️ Starting FastAPI backend..."

cd "$(dirname "$0")/../backend" || exit
source venv/Scripts/activate
uvicorn main:app --reload