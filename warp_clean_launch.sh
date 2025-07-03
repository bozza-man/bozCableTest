#!/bin/bash

echo "=== Cable Tester Warp Launcher ==="
echo ""

# Ensure tmux sessions are running
if ! tmux has-session -t cable_backend 2>/dev/null || ! tmux has-session -t cable_frontend 2>/dev/null; then
    echo "Starting cable tester sessions..."
    python3 cable_tester_manager.py tmux
    sleep 3
fi

echo "Creating new Warp window..."
echo "(Make sure to focus on the NEW window that opens)"
echo ""

# Open Warp with a specific command to ensure new window
open -a Warp

# Give Warp time to open
sleep 2

# Now send commands to create the layout
osascript << 'EOF'
tell application "Warp"
    activate
end tell

-- Wait a moment
delay 1

tell application "System Events"
    tell process "Warp"
        -- Create new window (this ensures we're in a fresh window)
        keystroke "n" using {command down}
        delay 2
        
        -- Clear any existing content
        keystroke "clear"
        keystroke return
        delay 0.5
        
        -- Attach to backend
        keystroke "tmux attach -t cable_backend"
        keystroke return
        delay 2
        
        -- Create horizontal split
        keystroke "d" using {command down, shift down}
        delay 1
        
        -- In new pane, attach to frontend
        keystroke "tmux attach -t cable_frontend"
        keystroke return
    end tell
end tell
EOF

echo "✅ Done! Look for the NEW Warp window with:"
echo ""
echo "┌─────────────────────────────┐"
echo "│  Backend Server (logs)      │"
echo "├─────────────────────────────┤"
echo "│  Frontend Console           │"
echo "│  (Enter commands here)      │"
echo "└─────────────────────────────┘"
echo ""
echo "Commands in frontend:"
echo "  1 = SSH connect"
echo "  2 = Security test"
echo "  3 = Performance test"
echo "  q = Quit"