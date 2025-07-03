#!/bin/bash

# Get the session name from argument or default
SESSION=${1:-cable_enhanced}

# Check if session exists
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "❌ Session '$SESSION' does not exist"
    echo ""
    echo "Available sessions:"
    tmux list-sessions 2>/dev/null || echo "  (no sessions found)"
    echo ""
    echo "Run one of the launch scripts first:"
    echo "  ./launch_enhanced.sh"
    echo "  ./launch_dev_mode.sh"
    echo "  ./launch_safe.sh"
    exit 1
fi

# Copy attach command to clipboard
ATTACH_CMD="tmux attach -t $SESSION"
echo "$ATTACH_CMD" | pbcopy

echo "📋 Command copied to clipboard: $ATTACH_CMD"
echo ""

# Open Warp
osascript << 'EOF'
tell application "Warp"
    activate
    
    -- Create new window
    tell application "System Events"
        delay 1
        keystroke "n" using {command down}
    end tell
end tell
EOF

echo "✅ Warp window opened"
echo ""
echo "Now just:"
echo "1. Click in the Warp window"
echo "2. Paste (⌘V)"
echo "3. Press Enter"
echo ""
echo "The command is already in your clipboard!"