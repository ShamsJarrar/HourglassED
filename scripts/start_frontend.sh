#!/bin/bash
echo "💻 Starting frontend (React / Vite)..."

cd "$(dirname "$0")/../frontend" || exit
npm run dev