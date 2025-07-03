#!/bin/bash

echo "=== Cable Tester 3-Pane Launcher ==="
echo ""
echo "This will create:"
echo "1. Backend server (top left)"
echo "2. Frontend console (bottom left)"
echo "3. Remote SSH (right) - when you press '1'"
echo ""

# Kill any existing sessions
tmux kill-session -t cable_three 2>/dev/null || true

# Create new session with backend
tmux new-session -d -s cable_three -n "CableTester" "source venv/bin/activate && python src/backend_server_logged.py"

# Split horizontally for frontend
tmux split-window -v -t cable_three:0 -p 40 "source venv/bin/activate && sleep 3 && python src/frontend_three_pane.py"

# Set pane titles
tmux select-pane -t cable_three:0.0 -T "Backend Server"
tmux select-pane -t cable_three:0.1 -T "Frontend Console"

# Enable pane borders and titles
tmux set -t cable_three pane-border-status top
tmux set -t cable_three pane-border-format "#{pane_index}: #{pane_title}"

echo "Opening in Warp..."

# Open Warp and attach to the session
osascript << 'EOF'
tell application "Warp"
    activate
    delay 1
    
    tell application "System Events"
        tell process "Warp"
            -- Create new window
            keystroke "n" using {command down}
            delay 2
            
            -- Attach to our three-pane session
            keystroke "tmux attach -t cable_three"
            keystroke return
        end tell
    end tell
end tell
EOF

echo ""
echo "✅ Warp window created with Cable Tester"
echo ""
echo "When you press '1' in the frontend, a third pane will appear:"
echo ""
echo "┌──────────────┬─────────────┐"
echo "│   Backend    │   Remote    │"
echo "│   Server     │   SSH       │"
echo "├──────────────┤  (appears   │"
echo "│   Frontend   │   after     │"
echo "│   Console    │   option 1) │"
echo "└──────────────┴─────────────┘"
echo ""
echo "The remote pane will show the SSH connection to the second Mac"