#!/bin/bash

echo "=== Cable Tester with Dynamic Terminal UI ==="
echo ""

# Kill existing sessions
tmux kill-session -t cable_dynamic 2>/dev/null || true

# Create new session with bash shell
echo "Starting dynamic cable tester..."
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

# Split horizontally for dynamic frontend
tmux split-window -v -t cable_dynamic:0.0 -p 70 -c "$PWD" bash

# Start dynamic frontend
tmux send-keys -t cable_dynamic:0.1 "source venv/bin/activate" C-m
sleep 0.5
tmux send-keys -t cable_dynamic:0.1 "sleep 3" C-m
tmux send-keys -t cable_dynamic:0.1 "python src/frontend_dynamic.py" C-m

# Set pane titles
tmux select-pane -t cable_dynamic:0.0 -T "Backend Server"
tmux select-pane -t cable_dynamic:0.1 -T "Dynamic Terminal UI"

# Enable pane borders
tmux set -t cable_dynamic pane-border-status top

# Focus on the dynamic UI pane
tmux select-pane -t cable_dynamic:0.1

echo ""
echo "✅ Dynamic Cable Tester launched"
echo ""
echo "Features:"
echo "• Cursor-based menu navigation (↑/↓ arrows)"
echo "• Live connection status display"
echo "• Real-time alerts at bottom"
echo "• Color-coded status indicators"
echo ""
echo "Controls:"
echo "• ↑/↓ - Navigate menu"
echo "• Enter - Select menu item"
echo "• q - Quit application"
echo ""

# Ask about opening
read -p "Open in new terminal? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Copy attach command to clipboard
    echo "tmux attach -t cable_dynamic" | pbcopy
    
    # Try to open in Warp if available, otherwise default terminal
    if command -v warp &> /dev/null || [ -d "/Applications/Warp.app" ]; then
        echo "Opening in Warp..."
        osascript -e 'tell application "Warp" to activate'
        osascript -e 'tell application "System Events" to keystroke "n" using {command down}'
        echo "📋 Paste the command (⌘V) and press Enter"
    else
        # Open in default terminal
        osascript -e 'tell application "Terminal" to do script "tmux attach -t cable_dynamic"'
    fi
else
    echo "You can attach manually with: tmux attach -t cable_dynamic"
fi