#!/bin/bash

echo "=== Cable Tester Warp Launcher ==="
echo ""

# Ensure tmux sessions are running
if ! tmux has-session -t cable_backend 2>/dev/null || ! tmux has-session -t cable_frontend 2>/dev/null; then
    echo "Starting cable tester sessions..."
    python3 cable_tester_manager.py tmux
    sleep 3
fi

echo "Opening Warp with cable tester..."

# Use a temporary AppleScript file to avoid heredoc issues
cat > /tmp/cable_warp.applescript << 'APPLESCRIPT'
tell application "Warp"
    activate
    delay 1
    
    tell application "System Events"
        tell process "Warp"
            -- New window
            keystroke "n" using {command down}
            delay 2
            
            -- Attach to backend
            keystroke "tmux attach -t cable_backend"
            keystroke return
            delay 1
            
            -- Split horizontally
            keystroke "d" using {command down, shift down}
            delay 1
            
            -- Attach to frontend
            keystroke "tmux attach -t cable_frontend"
            keystroke return
        end tell
    end tell
end tell
APPLESCRIPT

# Run the AppleScript
osascript /tmp/cable_warp.applescript

# Clean up
rm -f /tmp/cable_warp.applescript

echo ""
echo "✅ Warp should now show:"
echo "   Top pane:    Backend logs"
echo "   Bottom pane: Frontend console (interact here)"
echo ""
echo "If the window didn't open properly, you can manually:"
echo "1. Switch to Warp"
echo "2. The commands should already be running"