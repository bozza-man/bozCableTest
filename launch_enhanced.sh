#!/bin/bash

echo "=== Cable Tester with SSH Manager ==="
echo ""

# Kill existing sessions
tmux kill-session -t cable_enhanced 2>/dev/null || true

# Create new integrated session with bash shell
echo "Starting enhanced cable tester..."
tmux new-session -d -s cable_enhanced -n "CableTester" -c "$PWD" bash

# Verify session was created
if ! tmux has-session -t cable_enhanced 2>/dev/null; then
    echo "❌ Failed to create tmux session"
    exit 1
fi

# First pane already has a shell, so we can run commands
# Start backend in first pane
tmux send-keys -t cable_enhanced:0.0 "source venv/bin/activate" C-m
sleep 0.5

# Verify venv activated
BACKEND_CHECK=$(tmux capture-pane -t cable_enhanced:0.0 -p | tail -1)
echo "Backend pane check: $BACKEND_CHECK"

tmux send-keys -t cable_enhanced:0.0 "python src/backend_server_logged.py" C-m

# Split horizontally for enhanced frontend (also with bash shell)
tmux split-window -v -t cable_enhanced:0.0 -p 50 -c "$PWD" bash

# Verify split was created
if ! tmux list-panes -t cable_enhanced | grep -q "1:"; then
    echo "❌ Failed to create split pane"
    exit 1
fi

# Start enhanced frontend
tmux send-keys -t cable_enhanced:0.1 "source venv/bin/activate" C-m
sleep 0.5
tmux send-keys -t cable_enhanced:0.1 "sleep 3" C-m
tmux send-keys -t cable_enhanced:0.1 "python src/frontend_with_ssh_manager.py" C-m

# Set pane titles
tmux select-pane -t cable_enhanced:0.0 -T "Backend Server"
tmux select-pane -t cable_enhanced:0.1 -T "Frontend Console"

# Enable pane borders
tmux set -t cable_enhanced pane-border-status top

echo "Opening in Warp..."

# Copy command to clipboard
echo "tmux attach -t cable_enhanced" | pbcopy

# Open Warp with better timing
osascript << 'EOF'
tell application "Warp"
    activate
    delay 2
    
    tell application "System Events"
        tell process "Warp"
            -- Create new window
            keystroke "n" using {command down}
            delay 3
            
            -- Wait for window to be ready
            repeat 5 times
                if (exists window 1) then
                    exit repeat
                end if
                delay 0.5
            end repeat
            
            -- Paste and execute the command
            keystroke "v" using {command down}
            delay 0.5
            keystroke return
        end tell
    end tell
end tell
EOF

echo ""
echo "✅ Enhanced Cable Tester launched"
echo ""
echo "Features:"
echo "• SSH Server Management - Save and select servers"
echo "• Auto-creates third pane when connecting"
echo "• Remembers last used server"
echo ""
echo "Press '1' in the frontend to manage SSH servers"