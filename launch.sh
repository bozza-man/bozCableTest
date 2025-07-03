#!/bin/bash

# Quick launcher for Cable Tester

echo "Cable Tester Launcher"
echo "===================="
echo ""
echo "Select launch mode:"
echo "1) Warp - Connect to existing sessions (Recommended)"
echo "2) Warp - New split view (Backend | Frontend | Logs)"
echo "3) Terminal - Current terminal with tmux"
echo "4) Status - Check if running"
echo "5) Stop - Kill all sessions"
echo ""
echo -n "Enter choice (1-5): "
read choice

case $choice in
    1)
        ./warp_connect.sh
        ;;
    2)
        python3 warp_launcher.py split
        ;;
    3)
        echo "Attaching to frontend console..."
        echo "Press Ctrl+B then D to detach"
        sleep 2
        tmux attach -t cable_frontend || echo "No frontend session found"
        ;;
    4)
        python3 cable_tester_manager.py status
        ;;
    5)
        echo "Stopping all cable tester sessions..."
        tmux kill-session -t cable_backend 2>/dev/null || true
        tmux kill-session -t cable_frontend 2>/dev/null || true
        python3 warp_launcher.py kill 2>/dev/null || true
        echo "All sessions stopped"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac