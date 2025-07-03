#!/bin/bash

# Enhanced Warp launcher that connects to existing tmux sessions

echo "=== Cable Tester Warp Launcher ==="
echo ""

# Check if Warp is installed
if ! osascript -e 'tell application "System Events" to return exists application process "Warp"' &> /dev/null; then
    echo "Error: Warp terminal is not installed"
    echo "Please install Warp from https://www.warp.dev"
    exit 1
fi

# Check if tmux sessions exist
BACKEND_EXISTS=$(tmux has-session -t cable_backend 2>/dev/null && echo "yes" || echo "no")
FRONTEND_EXISTS=$(tmux has-session -t cable_frontend 2>/dev/null && echo "yes" || echo "no")

if [[ "$BACKEND_EXISTS" == "no" ]] || [[ "$FRONTEND_EXISTS" == "no" ]]; then
    echo "Cable tester sessions not found. Starting them..."
    python3 cable_tester_manager.py tmux
    echo "Waiting for services to start..."
    sleep 4
fi

echo "Opening Warp with horizontal split..."

# Create AppleScript for Warp
osascript <<'EOF'
tell application "Warp"
    activate
    delay 0.5
    
    -- Create new window
    tell application "System Events"
        tell process "Warp"
            -- New window
            keystroke "n" using {command down}
            delay 1.5
            
            -- Clear and attach to backend
            keystroke "clear"
            keystroke return
            delay 0.2
            
            keystroke "echo '=== BACKEND SERVER (Logs) ==='"
            keystroke return
            delay 0.2
            
            keystroke "tmux attach-session -t cable_backend"
            keystroke return
            delay 1
            
            -- Create horizontal split (Warp specific)
            keystroke "d" using {command down, shift down}
            delay 1.5
            
            -- In bottom pane, clear and attach to frontend
            keystroke "clear"
            keystroke return
            delay 0.2
            
            keystroke "echo '=== FRONTEND CONSOLE (Interact Here) ==='"
            keystroke return
            delay 0.2
            
            keystroke "tmux attach-session -t cable_frontend"
            keystroke return
        end tell
    end tell
end tell
EOF

echo ""
echo "✅ Warp window opened with cable tester"
echo ""
echo "Layout:"
echo "┌─────────────────────────────────────┐"
echo "│   BACKEND SERVER (Logs)             │"
echo "│   - Watch server activity here      │"
echo "├─────────────────────────────────────┤"
echo "│   FRONTEND CONSOLE (Interact)       │"
echo "│   - Enter commands here (1-5, q)    │"
echo "└─────────────────────────────────────┘"
echo ""
echo "Warp Navigation:"
echo "  • Switch panes: Cmd+Option+↑/↓"
echo "  • Resize panes: Drag the divider"
echo ""
echo "Tmux Controls:"
echo "  • Detach: Ctrl+B then D"
echo "  • Scroll: Ctrl+B then ["
echo "  • Exit scroll: q"
echo ""
echo "Cable Tester Commands (in frontend):"
echo "  1 - Connect SSH"
echo "  2 - Security test"
echo "  3 - Performance test"
echo "  4 - Status"
echo "  5 - Emergency stop"
echo "  q - Quit"