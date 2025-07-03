#!/bin/bash

echo "Restarting backend server..."

# Kill any existing backend process
pkill -f "backend_server_logged.py" 2>/dev/null

# Wait for process to die
sleep 2

# Send Ctrl+C to the tmux pane just in case
tmux send-keys -t cable_enhanced:0.0 C-c 2>/dev/null

# Wait for any output to finish
sleep 2

# Check if we need to get back to a shell prompt
PANE_OUTPUT=$(tmux capture-pane -t cable_enhanced:0.0 -p | tail -5)
echo "Checking pane state..."

# If we see shutdown messages but no prompt, we need to wait or respawn
if echo "$PANE_OUTPUT" | grep -q "Graceful shutdown complete" && ! echo "$PANE_OUTPUT" | grep -q '\$'; then
    echo "Backend has shut down but no shell prompt. Checking for shell..."
    # Try sending a newline to see if we get a prompt
    tmux send-keys -t cable_enhanced:0.0 C-m
    sleep 1
    
    # Check again
    LAST_LINE=$(tmux capture-pane -t cable_enhanced:0.0 -p | tail -1)
    if [[ ! "$LAST_LINE" =~ \$ ]]; then
        echo "Still no shell prompt, respawning pane..."
        tmux respawn-pane -t cable_enhanced:0.0 -k bash
        sleep 1
        # Set up the environment in the new shell
        tmux send-keys -t cable_enhanced:0.0 "cd /Users/danielborrowman/Documents/github/bozCableTest/cable_tester" C-m
        sleep 0.5
        tmux send-keys -t cable_enhanced:0.0 "source venv/bin/activate" C-m
        sleep 0.5
    fi
fi

# Clear the screen for clean output
tmux send-keys -t cable_enhanced:0.0 "clear" C-m
sleep 0.5

# Start the backend
tmux send-keys -t cable_enhanced:0.0 "python src/backend_server_logged.py" C-m

echo "Backend restart initiated. Waiting for startup..."

# Wait and verify the command was executed
sleep 1
BACKEND_OUTPUT=$(tmux capture-pane -t cable_enhanced:0.0 -p | tail -5)
echo "Backend pane output:"
echo "$BACKEND_OUTPUT"
echo "---"

sleep 3

# Check if it started
if tail -5 logs/backend_all.log | grep -q "USB monitoring started"; then
    echo "✅ Backend started successfully with USB monitoring"
else
    echo "⚠️  Backend may not have started properly. Check logs."
fi

echo "Done."