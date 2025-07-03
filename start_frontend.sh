#!/bin/bash

echo "Starting Cable Tester Frontend Console..."
echo "Make sure the backend is running first!"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies if needed
pip install websockets > /dev/null 2>&1

# Start the frontend (using fixed version)
python3 src/frontend_simple_fixed.py