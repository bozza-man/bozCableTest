#!/bin/bash

echo "Starting Cable Tester Backend Server..."
echo "The backend will run on ws://localhost:8765"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies if needed
pip install websockets > /dev/null 2>&1

# Start the backend (use the logged version)
echo "Starting backend server..."
echo "Press Ctrl+C to stop"
echo ""
python3 src/backend_server_logged.py

# When the backend exits, we'll return to the shell
echo ""
echo "Backend server stopped."