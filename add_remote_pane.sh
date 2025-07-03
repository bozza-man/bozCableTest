#!/bin/bash

# Script to add a third pane for remote SSH monitoring

REMOTE_HOST="${1:-192.168.1.100}"
REMOTE_USER="${2:-testuser}"

# Check if we're in the cable tester tmux session
CURRENT_SESSION=$(tmux display-message -p '#S' 2>/dev/null)

if [[ -z "$CURRENT_SESSION" ]]; then
    echo "Not in a tmux session"
    exit 1
fi

# Create a vertical split on the right (33% width)
tmux split-window -h -p 33

# Set the pane title
tmux select-pane -t '{right}' -T "Remote: $REMOTE_HOST"

# Send initial commands to the new pane
tmux send-keys -t '{right}' "clear" C-m
tmux send-keys -t '{right}' "echo '=== Remote SSH Connection ==='" C-m
tmux send-keys -t '{right}' "echo 'Host: $REMOTE_HOST'" C-m
tmux send-keys -t '{right}' "echo 'User: $REMOTE_USER'" C-m
tmux send-keys -t '{right}' "echo ''" C-m
tmux send-keys -t '{right}' "echo 'Connecting...'" C-m
tmux send-keys -t '{right}' "ssh $REMOTE_USER@$REMOTE_HOST" C-m

# Return focus to the frontend pane
tmux select-pane -t '.1'

echo "Remote pane created. Check the right side of your Warp window."