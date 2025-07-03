#!/bin/bash

echo "=== Cable Tester Safe Launch ==="
echo ""

# Function to launch in tmux
launch_session() {
    local session_name=$1
    local backend_script=$2
    local frontend_script=$3
    
    # Kill existing session
    tmux kill-session -t "$session_name" 2>/dev/null || true
    
    # Create new session
    echo "Creating tmux session: $session_name"
    tmux new-session -d -s "$session_name" -n "CableTester" -c "$PWD" bash
    
    # Start backend
    tmux send-keys -t "$session_name:0.0" "source venv/bin/activate" C-m
    sleep 0.5
    tmux send-keys -t "$session_name:0.0" "python $backend_script" C-m
    
    # Split for frontend
    tmux split-window -v -t "$session_name:0.0" -p 50 -c "$PWD" bash
    
    # Start frontend
    tmux send-keys -t "$session_name:0.1" "source venv/bin/activate" C-m
    tmux send-keys -t "$session_name:0.1" "sleep 3" C-m
    tmux send-keys -t "$session_name:0.1" "python $frontend_script" C-m
    
    # Set pane titles
    tmux select-pane -t "$session_name:0.0" -T "Backend Server"
    tmux select-pane -t "$session_name:0.1" -T "Frontend Console"
    
    # Enable pane borders
    tmux set -t "$session_name" pane-border-status top
}

# Menu for launch options
echo "Select launch mode:"
echo "1) Standard (with SSH manager)"
echo "2) Development (with hot reload)"
echo "3) Debug (with verbose logging)"
echo ""
read -p "Enter choice (1-3): " -n 1 -r
echo ""

case $REPLY in
    1)
        launch_session "cable_enhanced" "src/backend_server_logged.py" "src/frontend_with_ssh_manager.py"
        SESSION="cable_enhanced"
        ;;
    2)
        launch_session "cable_dev" "src/backend_with_reload.py" "src/frontend_with_reload.py"
        SESSION="cable_dev"
        
        # Add file watcher pane for dev mode
        tmux split-window -h -t "$SESSION:0.0" -p 40 -c "$PWD" bash
        tmux send-keys -t "$SESSION:0.2" "source venv/bin/activate" C-m
        tmux send-keys -t "$SESSION:0.2" "sleep 5 && python src/file_watcher.py" C-m
        tmux select-pane -t "$SESSION:0.2" -T "File Watcher"
        ;;
    3)
        launch_session "cable_debug" "src/backend_server_logged.py --debug" "src/frontend_with_ssh_manager.py"
        SESSION="cable_debug"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Session '$SESSION' created successfully!"
echo ""

# Copy attach command to clipboard
ATTACH_CMD="tmux attach -t $SESSION"
echo "$ATTACH_CMD" | pbcopy

echo "The attach command has been copied to your clipboard."
echo ""
echo "Options to connect:"
echo "1) Open a new terminal and paste (⌘V)"
echo "2) Run: $ATTACH_CMD"
echo ""

# Ask about opening Warp
read -p "Open new Warp window? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Just open Warp, don't try to type
    osascript -e 'tell application "Warp" to activate'
    osascript -e 'tell application "System Events" to keystroke "n" using {command down}'
    
    echo ""
    echo "✅ New Warp window opened"
    echo "📋 Paste the command (⌘V) and press Enter"
else
    echo "You can attach manually with: $ATTACH_CMD"
fi