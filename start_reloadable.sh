#!/bin/bash

echo "=== Cable Tester with Hot Reload Support ==="
echo ""
echo "This version supports in-place code updates without losing connections!"
echo ""

# Kill existing sessions
tmux kill-session -t cable_reload 2>/dev/null || true

# Create new session with reloadable backend
echo "Starting reloadable servers..."
tmux new-session -d -s cable_reload -n "CableReload" -c "$PWD" bash

# Start reloadable backend in first pane
tmux send-keys -t cable_reload:0.0 "source venv/bin/activate" C-m
sleep 0.5
tmux send-keys -t cable_reload:0.0 "python src/backend_with_reload.py" C-m

# Split horizontally for reloadable frontend
tmux split-window -v -t cable_reload:0.0 -p 50 -c "$PWD" bash

# Start reloadable frontend
tmux send-keys -t cable_reload:0.1 "source venv/bin/activate" C-m
tmux send-keys -t cable_reload:0.1 "sleep 3" C-m
tmux send-keys -t cable_reload:0.1 "python src/frontend_with_reload.py" C-m

# Set pane titles
tmux select-pane -t cable_reload:0.0 -T "Reloadable Backend"
tmux select-pane -t cable_reload:0.1 -T "Reloadable Frontend"

# Enable pane borders
tmux set -t cable_reload pane-border-status top

echo ""
echo "✅ Reloadable servers launched!"
echo ""
echo "To connect: tmux attach -t cable_reload"
echo ""
echo "Hot Reload Commands:"
echo "  • In frontend: Type 'reload' to reload frontend code"
echo "  • In frontend: Type 'reload-backend' to reload backend code"
echo "  • Changes to Python files will be loaded without losing connections!"
echo ""

# Optionally open in Warp
read -p "Open in Warp terminal? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    osascript << 'EOF'
tell application "Warp"
    activate
    delay 1
    
    tell application "System Events"
        tell process "Warp"
            -- Create new window
            keystroke "n" using {command down}
            delay 2
            
            -- Attach to session
            keystroke "tmux attach -t cable_reload"
            keystroke return
        end tell
    end tell
end tell
EOF
fi