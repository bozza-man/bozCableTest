#!/bin/bash

echo "Restarting frontend..."

# Send Ctrl+C to stop the frontend
tmux send-keys -t cable_enhanced:0.1 C-c 2>/dev/null

# Wait a moment
sleep 1

# Clear the pane
tmux send-keys -t cable_enhanced:0.1 "clear" C-m

# Start the frontend
tmux send-keys -t cable_enhanced:0.1 "python src/frontend_with_ssh_manager.py" C-m

echo "Frontend restart initiated."
echo "Done."