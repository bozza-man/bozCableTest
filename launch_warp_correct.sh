#!/bin/bash

echo "=== Cable Tester Warp Launcher ==="
echo ""

# Ensure tmux sessions are running
if ! tmux has-session -t cable_backend 2>/dev/null || ! tmux has-session -t cable_frontend 2>/dev/null; then
    echo "Starting cable tester sessions..."
    python3 cable_tester_manager.py tmux
    sleep 3
fi

echo "Opening new Warp window with cable tester..."

# Create AppleScript that properly targets the new window
cat > /tmp/cable_warp_fixed.applescript << 'APPLESCRIPT'
tell application "Warp"
    activate
    
    -- Create new window first
    tell application "System Events"
        tell process "Warp"
            keystroke "n" using {command down}
        end tell
    end tell
    
    -- Wait for new window
    delay 2
    
    -- Now work in the new window
    tell application "System Events"
        tell process "Warp"
            -- Type backend attach command
            keystroke "tmux attach -t cable_backend"
            keystroke return
            
            -- Wait for tmux to attach
            delay 2
            
            -- Create split in THIS window
            keystroke "d" using {command down, shift down}
            
            -- Wait for split
            delay 1
            
            -- Now in bottom pane, attach to frontend
            keystroke "tmux attach -t cable_frontend"
            keystroke return
        end tell
    end tell
end tell
APPLESCRIPT

# Run the AppleScript
osascript /tmp/cable_warp_fixed.applescript

# Clean up
rm -f /tmp/cable_warp_fixed.applescript

echo ""
echo "✅ A new Warp window should now have:"
echo "   Top pane:    Backend logs"
echo "   Bottom pane: Frontend console (interact here)"
echo ""
echo "Navigation:"
echo "  • Switch panes: Cmd+Option+↑/↓"
echo "  • Focus on bottom pane to enter commands"