#!/bin/bash
echo "Starting FinGuru Backend..."
echo

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
echo "Checking dependencies..."
pip install -q -r requirements.txt

# Start server
echo
echo "Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

