#!/bin/bash

echo "=== Cable Tester Development Mode ==="
echo "🔥 Hot reload enabled - changes to code will automatically reload!"
echo ""

# Kill existing sessions
tmux kill-session -t cable_dev 2>/dev/null || true

# Create new session with 4 panes
echo "Creating development environment..."
tmux new-session -d -s cable_dev -n "CableDev" -c "$PWD" bash

# Pane 0: Reloadable backend
tmux send-keys -t cable_dev:0.0 "source venv/bin/activate" C-m
sleep 0.5
tmux send-keys -t cable_dev:0.0 "echo '=== Reloadable Backend Server ==='" C-m
tmux send-keys -t cable_dev:0.0 "python src/backend_with_reload.py" C-m

# Split horizontally for frontend
tmux split-window -v -t cable_dev:0.0 -p 50 -c "$PWD" bash

# Pane 1: Reloadable frontend
tmux send-keys -t cable_dev:0.1 "source venv/bin/activate" C-m
tmux send-keys -t cable_dev:0.1 "echo '=== Reloadable Frontend ==='" C-m
tmux send-keys -t cable_dev:0.1 "sleep 3 && python src/frontend_with_reload.py" C-m

# Split vertically for file watcher
tmux split-window -h -t cable_dev:0.0 -p 40 -c "$PWD" bash

# Pane 2: File watcher
tmux send-keys -t cable_dev:0.2 "source venv/bin/activate" C-m
tmux send-keys -t cable_dev:0.2 "echo '=== File Watcher ==='" C-m
tmux send-keys -t cable_dev:0.2 "sleep 5 && python src/file_watcher.py" C-m

# Split the bottom pane for logs
tmux split-window -h -t cable_dev:0.1 -p 40 -c "$PWD" bash

# Pane 3: Log viewer
tmux send-keys -t cable_dev:0.3 "echo '=== Live Logs ==='" C-m
tmux send-keys -t cable_dev:0.3 "tail -f logs/backend_all.log | grep -E '(ERROR|WARNING|reload|Reload)' --color=always" C-m

# Set pane titles
tmux select-pane -t cable_dev:0.0 -T "Backend (Reloadable)"
tmux select-pane -t cable_dev:0.1 -T "Frontend (Reloadable)"
tmux select-pane -t cable_dev:0.2 -T "File Watcher"
tmux select-pane -t cable_dev:0.3 -T "Live Logs"

# Enable pane borders
tmux set -t cable_dev pane-border-status top

# Set active pane to frontend
tmux select-pane -t cable_dev:0.1

echo ""
echo "✅ Development environment ready!"
echo ""
echo "Layout:"
echo "┌─────────────────┬─────────────────┐"
echo "│ Backend Server  │ File Watcher    │"
echo "├─────────────────┼─────────────────┤"
echo "│ Frontend        │ Live Logs       │"
echo "└─────────────────┴─────────────────┘"
echo ""
echo "Features:"
echo "  • 🔄 Automatic reload when Python files change"
echo "  • 📝 Live log monitoring (errors/warnings)"
echo "  • 🔌 WebSocket connections preserved during reload"
echo "  • 🚀 Zero-downtime code updates"
echo ""
echo "Commands:"
echo "  • Frontend: 'reload' to manually reload frontend"
echo "  • Frontend: 'reload-backend' to manually reload backend"
echo "  • Or just save your Python files - they'll auto-reload!"
echo ""

# Ask to open in terminal
read -p "Open in Warp terminal? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Copy command to clipboard
    echo "tmux attach -t cable_dev" | pbcopy
    
    # Open Warp with more reliable timing
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
    echo "✅ Command copied to clipboard and Warp opened"
    echo "If the command didn't execute, just paste (⌘V) and press Enter"
else
    echo "To attach manually: tmux attach -t cable_dev"
fi