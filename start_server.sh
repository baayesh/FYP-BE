#!/bin/bash

# Navigate to project directory
cd /Users/ayeshbamunuarachchi/Documents/projects/FYP/retinify_backend

# Activate virtual environment
source .venv/bin/activate

# Start the server without reload (to avoid WatchFiles issues)
echo "Starting FastAPI server on http://127.0.0.1:8000"
echo "API Documentation: http://127.0.0.1:8000/docs"
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn main:app --host 127.0.0.1 --port 8000
