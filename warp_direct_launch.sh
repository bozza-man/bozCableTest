#!/bin/bash

echo "=== Cable Tester Direct Warp Launcher ==="
echo ""

# Kill existing sessions
tmux kill-session -t cable_enhanced 2>/dev/null || true

# Create new integrated session
echo "Starting enhanced cable tester..."
tmux new-session -d -s cable_enhanced -n "CableTester"

# Start backend in first pane
tmux send-keys -t cable_enhanced:0.0 "source venv/bin/activate" C-m
tmux send-keys -t cable_enhanced:0.0 "python src/backend_server_logged.py" C-m

# Split horizontally for enhanced frontend
tmux split-window -v -t cable_enhanced:0.0 -p 50

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
echo "Session created!"
echo ""

# Try using open command with Warp
echo "Attempting to open Warp and attach to session..."

# First, just open Warp
open -a "Warp"

# Wait for Warp to open
sleep 2

# Now use a more reliable AppleScript approach
osascript -e 'tell application "Warp" to activate'
sleep 1

# Try using system events to paste the command
osascript << 'EOF'
tell application "System Events"
    tell process "Warp"
        keystroke "n" using {command down}
        delay 2
        -- Use paste instead of typing
        set the clipboard to "tmux attach -t cable_enhanced"
        keystroke "v" using {command down}
        delay 0.5
        keystroke return
    end tell
end tell
EOF

echo ""
echo "✅ Warp should now be open with the cable tester"
echo ""
echo "If automatic attachment failed, please:"
echo "1. Click on the new Warp window"
echo "2. Type: tmux attach -t cable_enhanced"
echo "3. Press Enter"
echo ""
echo "The session is running and ready to attach!"