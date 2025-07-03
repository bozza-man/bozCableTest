#!/bin/bash

echo "=== Cable Tester with Dynamic UI & SSH Manager ==="
echo ""

# Check if port 8765 is in use
if lsof -i :8765 >/dev/null 2>&1; then
    echo "⚠️  Port 8765 is already in use"
    echo ""
    read -p "Kill existing backend processes? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./cleanup_backend.sh
    else
        echo "❌ Cannot start - port is in use"
        exit 1
    fi
fi

# Kill existing sessions
tmux kill-session -t cable_dynamic 2>/dev/null || true

# Create new integrated session with bash shell
echo "Starting enhanced dynamic cable tester..."
tmux new-session -d -s cable_dynamic -n "CableTester" -c "$PWD" bash

# Verify session was created
if ! tmux has-session -t cable_dynamic 2>/dev/null; then
    echo "❌ Failed to create tmux session"
    exit 1
fi

# Start backend in first pane
tmux send-keys -t cable_dynamic:0.0 "source venv/bin/activate" C-m
sleep 0.5
tmux send-keys -t cable_dynamic:0.0 "python src/backend_server_logged.py" C-m

# Split horizontally for dynamic frontend with SSH manager
tmux split-window -v -t cable_dynamic:0.0 -p 70 -c "$PWD" bash

# Start optimized dynamic frontend
tmux send-keys -t cable_dynamic:0.1 "source venv/bin/activate" C-m
sleep 0.5
tmux send-keys -t cable_dynamic:0.1 "sleep 3" C-m
tmux send-keys -t cable_dynamic:0.1 "python src/frontend_dynamic_optimized.py" C-m

# Set pane titles
tmux select-pane -t cable_dynamic:0.0 -T "Backend Server"
tmux select-pane -t cable_dynamic:0.1 -T "Dynamic Terminal UI"

# Enable pane borders
tmux set -t cable_dynamic pane-border-status top

# Focus on the dynamic UI pane
tmux select-pane -t cable_dynamic:0.1

echo "Opening in Warp..."

# Copy command to clipboard
echo "tmux attach -t cable_dynamic" | pbcopy

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
echo "✅ Enhanced Dynamic Cable Tester launched"
echo ""
echo "Features:"
echo "• Dynamic terminal UI with cursor navigation"
echo "• SSH Server Management built-in"
echo "• Live connection status and alerts"
echo "• Auto-creates third pane when connecting"
echo ""
echo "Controls:"
echo "• ↑/↓ - Navigate menu"
echo "• Enter - Select menu item"
echo "• ESC - Back (in SSH menu)"
echo "• q - Quit application"