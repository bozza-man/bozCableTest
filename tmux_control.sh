#!/bin/bash

echo "=== Cable Tester Tmux Control ==="
echo ""
echo "Backend and Frontend are running in tmux sessions."
echo ""
echo "Available commands:"
echo "  1 - View backend session"
echo "  2 - View frontend session"
echo "  3 - Send command to frontend"
echo "  4 - Show both sessions status"
echo "  5 - Stop both sessions"
echo ""
echo "Enter choice (1-5): "
read choice

case $choice in
    1)
        echo "Attaching to backend session (press Ctrl+B then D to detach)..."
        sleep 2
        tmux attach-session -t backend
        ;;
    2)
        echo "Attaching to frontend session (press Ctrl+B then D to detach)..."
        sleep 2
        tmux attach-session -t frontend
        ;;
    3)
        echo "What command to send to frontend? (1-5 or q): "
        read cmd
        tmux send-keys -t frontend "$cmd" C-m
        echo "Command sent!"
        sleep 1
        echo "Frontend output:"
        tmux capture-pane -t frontend -p | tail -20
        ;;
    4)
        echo "=== Backend Status ==="
        tmux capture-pane -t backend -p | tail -10
        echo ""
        echo "=== Frontend Status ==="
        tmux capture-pane -t frontend -p | tail -10
        ;;
    5)
        echo "Stopping both sessions..."
        tmux send-keys -t frontend "q" C-m
        sleep 1
        tmux kill-session -t frontend
        tmux kill-session -t backend
        echo "Sessions stopped."
        ;;
    *)
        echo "Invalid choice"
        ;;
esac