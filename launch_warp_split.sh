#!/bin/bash

# Launch Cable Tester in Warp with horizontal split showing both tmux sessions

CABLE_TESTER_DIR="$(cd "$(dirname "$0")" && pwd)"

# First, ensure the cable tester is running
echo "Ensuring cable tester is running..."
if ! tmux has-session -t cable_backend 2>/dev/null; then
    echo "Starting cable tester sessions..."
    python3 cable_tester_manager.py tmux
    sleep 3
else
    echo "Cable tester sessions already running"
fi

# Now open Warp with split view
echo "Opening Warp with split view..."

osascript <<EOF
tell application "Warp"
    activate
    
    -- Create new window
    tell application "System Events"
        -- New window
        keystroke "n" using {command down}
        delay 1
        
        -- Connect to backend tmux session
        keystroke "tmux attach -t cable_backend"
        keystroke return
        delay 1
        
        -- Create horizontal split
        keystroke "d" using {command down, shift down}
        delay 1
        
        -- In the new pane, connect to frontend tmux session
        keystroke "tmux attach -t cable_frontend"
        keystroke return
    end tell
end tell
EOF

echo ""
echo "Warp window opened with:"
echo "  Top pane:    Backend server (logs)"
echo "  Bottom pane: Frontend console (interact here)"
echo ""
echo "Controls:"
echo "  Switch panes in Warp: Cmd+Option+Arrow"
echo "  Detach from tmux: Ctrl+B then D"
echo "  Quit frontend: Press 'q' in bottom pane"