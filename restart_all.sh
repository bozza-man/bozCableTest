#!/bin/bash

echo "=== Restarting Cable Tester ==="
echo ""

# First restart the backend
./restart_backend.sh

# Wait for backend to be ready
echo ""
echo "Waiting for backend to be ready..."
sleep 3

# Then restart the frontend
./restart_frontend.sh

echo ""
echo "✅ Cable Tester restarted"
echo ""
echo "To view the session:"
echo "  tmux attach -t cable_enhanced"