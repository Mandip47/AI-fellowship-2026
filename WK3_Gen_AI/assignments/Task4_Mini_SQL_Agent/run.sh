#!/bin/bash
# ==============================================================================
# Helper script to launch the FastAPI SQL Agent API
# ==============================================================================

# Get current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment (.venv) not found. Setting it up..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Starting SQL Agent FastAPI Service..."
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
