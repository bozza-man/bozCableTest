#!/bin/zsh

# Cable Tester Warp Terminal Launcher
# This script creates a new Warp window with split panes for backend and frontend

CABLE_TESTER_DIR="$(cd "$(dirname "$0")" && pwd)"

# Function to create Warp window with cable tester
launch_cable_tester_in_warp() {
    echo "Launching Cable Tester in Warp Terminal..."
    
    # Create tmux configuration for cable tester
    cat > /tmp/cable_tester_tmux.conf <<EOF
# Cable Tester tmux configuration
set -g mouse on
set -g status-style bg=blue,fg=white
set -g window-status-current-style bg=red,fg=white
set -g pane-border-style fg=blue
set -g pane-active-border-style fg=red

# Set pane titles
set -g pane-border-status top
set -g pane-border-format "#{pane_index}: #{pane_title}"
EOF

    # AppleScript to control Warp
    osascript <<EOF
tell application "Warp"
    activate
    
    -- Create new window
    tell application "System Events"
        keystroke "n" using {command down}
        delay 1
        
        -- Start tmux with custom layout
        keystroke "cd $CABLE_TESTER_DIR"
        keystroke return
        delay 0.5
        
        -- Create tmux session with custom config
        keystroke "tmux -f /tmp/cable_tester_tmux.conf new-session -s cable_tester -n 'Cable Tester' \\; split-window -h -p 50"
        keystroke return
        delay 1
        
        -- Setup left pane (Backend)
        keystroke "printf '\\033]2;Backend Server\\033\\\\'"
        keystroke return
        keystroke "source venv/bin/activate"
        keystroke return
        keystroke "clear"
        keystroke return
        keystroke "echo '=== Cable Tester Backend ==='"
        keystroke return
        keystroke "echo 'Starting backend server...'"
        keystroke return
        keystroke "echo ''"
        keystroke return
        keystroke "python src/backend_server_logged.py"
        keystroke return
        
        -- Switch to right pane
        keystroke "b" using {control down}
        keystroke "o"
        delay 0.5
        
        -- Setup right pane (Frontend)
        keystroke "printf '\\033]2;Frontend Console\\033\\\\'"
        keystroke return
        keystroke "source venv/bin/activate"
        keystroke return
        keystroke "clear"
        keystroke return
        keystroke "echo '=== Cable Tester Frontend ==='"
        keystroke return
        keystroke "echo 'Waiting for backend to start...'"
        keystroke return
        keystroke "sleep 3"
        keystroke return
        keystroke "python src/frontend_simple_fixed.py"
        keystroke return
    end tell
end tell
EOF

    echo "Cable Tester launched in Warp!"
    echo ""
    echo "Tmux controls:"
    echo "  - Switch panes: Ctrl+B then O"
    echo "  - Resize panes: Ctrl+B then Ctrl+Arrow"
    echo "  - Detach session: Ctrl+B then D"
    echo "  - Reattach: tmux attach -t cable_tester"
}

# Check if Warp is installed
if ! osascript -e 'tell application "System Events" to return exists application process "Warp"' &> /dev/null; then
    echo "Error: Warp terminal is not installed"
    echo "Please install Warp from https://www.warp.dev"
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f "cable_tester_manager.py" ]; then
    echo "Error: This script must be run from the cable_tester directory"
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Launch the cable tester
launch_cable_tester_in_warp