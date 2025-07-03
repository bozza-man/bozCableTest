#!/bin/bash

echo "=== Cable Tester Manual Warp Launcher ==="
echo ""

# Kill existing sessions
tmux kill-session -t cable_enhanced 2>/dev/null || true

# Create new integrated session
echo "Creating tmux session..."
tmux new-session -d -s cable_enhanced -n "CableTester" -c "$PWD" bash

# Start backend in first pane
tmux send-keys -t cable_enhanced:0.0 "source venv/bin/activate" C-m
tmux send-keys -t cable_enhanced:0.0 "python src/backend_server_logged.py" C-m

# Split horizontally for enhanced frontend (with bash shell)
tmux split-window -v -t cable_enhanced:0.0 -p 50 -c "$PWD" bash

# Start enhanced frontend
tmux send-keys -t cable_enhanced:0.1 "source venv/bin/activate" C-m
tmux send-keys -t cable_enhanced:0.1 "sleep 3" C-m
tmux send-keys -t cable_enhanced:0.1 "python src/frontend_with_ssh_manager.py" C-m

# Set pane titles
tmux select-pane -t cable_enhanced:0.0 -T "Backend Server"
tmux select-pane -t cable_enhanced:0.1 -T "Frontend Console"

# Enable pane borders
tmux set -t cable_enhanced pane-border-status top

echo ""
echo "✅ Session 'cable_enhanced' created successfully!"
echo ""

# Try to open Warp
echo "Opening Warp..."
open -a "Warp" 2>/dev/null || echo "Note: Could not auto-open Warp"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "To attach to the cable tester session:"
echo ""
echo "1. In Warp, create a new window (⌘N)"
echo "2. Type this command:"
echo ""
echo "   tmux attach -t cable_enhanced"
echo ""
echo "3. Press Enter"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "The session will show:"
echo "• Top pane: Backend Server"
echo "• Bottom pane: Frontend Console with SSH Manager"
echo ""
echo "When you select option 1 in the frontend, a third pane"
echo "will automatically be created for the SSH connection."
echo ""

# Also try to copy the command to clipboard for convenience
echo "tmux attach -t cable_enhanced" | pbcopy 2>/dev/null && echo "✨ Command copied to clipboard!"