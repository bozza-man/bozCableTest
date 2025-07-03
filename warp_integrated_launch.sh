#!/bin/bash

echo "=== Cable Tester Integrated 3-Pane Launcher ==="
echo ""

# Kill existing separate sessions
tmux kill-session -t cable_backend 2>/dev/null || true
tmux kill-session -t cable_frontend 2>/dev/null || true
tmux kill-session -t cable_integrated 2>/dev/null || true

# Create new integrated session
echo "Starting integrated cable tester session..."
tmux new-session -d -s cable_integrated -n "CableTester"

# Start backend in first pane
tmux send-keys -t cable_integrated:0.0 "source venv/bin/activate" C-m
tmux send-keys -t cable_integrated:0.0 "python src/backend_server_logged.py" C-m

# Split horizontally for frontend
tmux split-window -v -t cable_integrated:0.0 -p 40

# Start frontend in second pane
tmux send-keys -t cable_integrated:0.1 "source venv/bin/activate" C-m
tmux send-keys -t cable_integrated:0.1 "sleep 3" C-m
tmux send-keys -t cable_integrated:0.1 "python src/frontend_simple_fixed.py" C-m

# Set pane titles
tmux select-pane -t cable_integrated:0.0 -T "Backend Server"
tmux select-pane -t cable_integrated:0.1 -T "Frontend Console"

# Enable pane borders
tmux set -t cable_integrated pane-border-status top

# Create a script that will be executed when option 1 is selected
cat > /tmp/add_ssh_pane.sh << 'SCRIPT'
#!/bin/bash
# Check if third pane already exists
PANE_COUNT=$(tmux list-panes -t cable_integrated:0 | wc -l)
if [ $PANE_COUNT -lt 3 ]; then
    tmux split-window -h -t cable_integrated:0.0 -p 33
    tmux select-pane -t cable_integrated:0.2 -T "Remote SSH"
    tmux send-keys -t cable_integrated:0.2 "echo '=== Remote SSH Connection ==='" C-m
    tmux send-keys -t cable_integrated:0.2 "echo 'Enter SSH details when prompted'" C-m
    tmux send-keys -t cable_integrated:0.2 "echo ''" C-m
    tmux send-keys -t cable_integrated:0.2 "ssh testuser@192.168.1.100" C-m
    tmux select-pane -t cable_integrated:0.1
fi
SCRIPT
chmod +x /tmp/add_ssh_pane.sh

echo "Opening in Warp..."

# Open Warp with the integrated session
osascript << 'EOF'
tell application "Warp"
    activate
    delay 1
    
    tell application "System Events"
        tell process "Warp"
            -- Create new window
            keystroke "n" using {command down}
            delay 2
            
            -- Attach to integrated session
            keystroke "tmux attach -t cable_integrated"
            keystroke return
        end tell
    end tell
end tell
EOF

echo ""
echo "✅ Cable Tester launched in Warp"
echo ""
echo "Layout:"
echo "┌────────────────────────────┐"
echo "│     Backend Server         │"
echo "├────────────────────────────┤"
echo "│     Frontend Console       │"
echo "└────────────────────────────┘"
echo ""
echo "When you select option 1 (SSH Connect), run this in another terminal:"
echo "  /tmp/add_ssh_pane.sh"
echo ""
echo "This will create:"
echo "┌──────────────┬─────────────┐"
echo "│   Backend    │   Remote    │"
echo "│   Server     │   SSH       │"
echo "├──────────────┤ Connection  │"
echo "│   Frontend   │             │"
echo "│   Console    │             │"
echo "└──────────────┴─────────────┘"