#!/bin/bash

echo "=== Cable Tester with SSH Manager - Warp Launcher ==="
echo ""

# Kill existing sessions
tmux kill-session -t cable_enhanced 2>/dev/null || true

# Create new integrated session
echo "Starting enhanced cable tester..."
tmux new-session -d -s cable_enhanced -n "CableTester"

# Start backend in first pane
tmux send-keys -t cable_enhanced:0.0 "source venv/bin/activate" C-m
tmux send-keys -t cable_enhanced:0.0 "python src/backend_server_logged.py" C-m

# Split horizontally for enhanced frontend
tmux split-window -v -t cable_enhanced:0.0 -p 50

# Start enhanced frontend
tmux send-keys -t cable_enhanced:0.1 "source venv/bin/activate" C-m
tmux send-keys -t cable_enhanced:0.1 "sleep 3" C-m
tmux send-keys -t cable_enhanced:0.1 "python src/frontend_with_ssh_manager.py" C-m

# Set pane titles
tmux select-pane -t cable_enhanced:0.0 -T "Backend Server"
tmux select-pane -t cable_enhanced:0.1 -T "Frontend Console"

# Enable pane borders
tmux set -t cable_enhanced pane-border-status top

echo ""
echo "Session created successfully!"
echo ""

# Create a temporary AppleScript file instead of using heredoc
cat > /tmp/warp_launcher.applescript << 'APPLESCRIPT'
on run
    tell application "Warp"
        activate
        delay 1
    end tell
    
    delay 1
    
    tell application "System Events"
        tell process "Warp"
            -- Create new window
            keystroke "n" using {command down}
        end tell
    end tell
    
    delay 2
    
    tell application "System Events"
        tell process "Warp"
            -- Type the tmux command
            keystroke "t"
            keystroke "m"
            keystroke "u"
            keystroke "x"
            keystroke " "
            keystroke "a"
            keystroke "t"
            keystroke "t"
            keystroke "a"
            keystroke "c"
            keystroke "h"
            keystroke " "
            keystroke "-"
            keystroke "t"
            keystroke " "
            keystroke "c"
            keystroke "a"
            keystroke "b"
            keystroke "l"
            keystroke "e"
            keystroke "_"
            keystroke "e"
            keystroke "n"
            keystroke "h"
            keystroke "a"
            keystroke "n"
            keystroke "c"
            keystroke "e"
            keystroke "d"
            keystroke return
        end tell
    end tell
end run
APPLESCRIPT

echo "Opening in Warp..."
osascript /tmp/warp_launcher.applescript

# Clean up
rm -f /tmp/warp_launcher.applescript

echo ""
echo "✅ Enhanced Cable Tester launched"
echo ""
echo "Features:"
echo "• SSH Server Management - Save and select servers"
echo "• Auto-creates third pane when connecting"
echo "• Remembers last used server"
echo ""
echo "Press '1' in the frontend to manage SSH servers"
echo ""
echo "If the Warp window doesn't attach automatically, manually run:"
echo "  tmux attach -t cable_enhanced"