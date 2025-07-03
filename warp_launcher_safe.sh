#!/bin/bash

echo "=== Cable Tester Warp Launcher ==="
echo ""

# Check if Warp exists
if [ ! -d "/Applications/Warp.app" ]; then
    echo "❌ Error: Warp is not installed"
    echo "Please install from: https://www.warp.dev"
    echo ""
    echo "Alternative: Use tmux in current terminal"
    echo "Run: tmux attach -t cable_frontend"
    exit 1
fi

# Check if tmux sessions exist
if ! tmux has-session -t cable_backend 2>/dev/null || ! tmux has-session -t cable_frontend 2>/dev/null; then
    echo "Starting cable tester sessions..."
    python3 cable_tester_manager.py tmux
    sleep 3
fi

echo "Attempting to open Warp..."

# Try to open Warp first
open -a Warp

# Wait for Warp to start
sleep 2

# Now run the AppleScript
osascript <<'EOF' 2>/dev/null
tell application "Warp"
    activate
    delay 1
    
    tell application "System Events"
        tell process "Warp"
            -- Create new window
            keystroke "n" using {command down}
            delay 2
            
            -- Type the tmux attach command for backend
            keystroke "tmux attach -t cable_backend"
            keystroke return
            delay 1
            
            -- Create horizontal split
            keystroke "d" using {command down, shift down}
            delay 1
            
            -- Attach to frontend in bottom pane
            keystroke "tmux attach -t cable_frontend"
            keystroke return
        end tell
    end tell
end tell
EOF

if [ $? -eq 0 ]; then
    echo "✅ Successfully opened Warp with cable tester"
else
    echo "⚠️  Failed to automate Warp window"
    echo ""
    echo "Manual steps:"
    echo "1. Open Warp"
    echo "2. Create new window (Cmd+N)"
    echo "3. Run: tmux attach -t cable_backend"
    echo "4. Split horizontally (Cmd+Shift+D)"
    echo "5. In bottom pane run: tmux attach -t cable_frontend"
fi

echo ""
echo "Current tmux sessions:"
tmux list-sessions 2>/dev/null || echo "No sessions found"