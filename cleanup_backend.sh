#!/bin/bash

echo "🧹 Cleaning up backend processes..."

# Kill processes using port 8765
PORT_PIDS=$(lsof -ti :8765)
if [ -n "$PORT_PIDS" ]; then
    echo "Found processes using port 8765: $PORT_PIDS"
    echo "Killing processes..."
    kill -9 $PORT_PIDS 2>/dev/null
    sleep 1
fi

# Kill any Python backend processes
BACKEND_PIDS=$(ps aux | grep -E "python.*backend_server" | grep -v grep | awk '{print $2}')
if [ -n "$BACKEND_PIDS" ]; then
    echo "Found backend processes: $BACKEND_PIDS"
    echo "Killing backend processes..."
    kill -9 $BACKEND_PIDS 2>/dev/null
    sleep 1
fi

# Verify port is free
if lsof -i :8765 >/dev/null 2>&1; then
    echo "❌ Warning: Port 8765 is still in use"
else
    echo "✅ Port 8765 is now free"
fi

# Kill specific tmux sessions if requested
if [ "$1" = "--kill-sessions" ]; then
    echo ""
    echo "Killing tmux sessions..."
    for session in cable_dev cable_dynamic cable_enhanced; do
        if tmux has-session -t "$session" 2>/dev/null; then
            echo "  Killing session: $session"
            tmux kill-session -t "$session"
        fi
    done
fi

echo ""
echo "🧹 Cleanup complete!"