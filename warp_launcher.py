#!/usr/bin/env python3

import subprocess
import sys
import time
import argparse
from pathlib import Path

class WarpLauncher:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.tmux_config = self.base_dir / ".cable_tester_tmux.conf"
        
    def create_tmux_config(self, layout="split"):
        """Create custom tmux configuration"""
        config = """
# Cable Tester tmux configuration
set -g mouse on
set -g history-limit 10000

# Status bar
set -g status-style bg=colour235,fg=colour246
set -g status-left '#[fg=colour232,bg=colour39,bold] Cable Tester #[fg=colour39,bg=colour235,nobold]'
set -g status-right '#[fg=colour235,bg=colour241]#[fg=colour233,bg=colour241,bold] %H:%M:%S '
set -g status-right-length 50
set -g status-left-length 20

# Window status
set -g window-status-current-style bg=colour39,fg=colour232,bold
set -g window-status-current-format ' #I:#W#F '
set -g window-status-format ' #I:#W#F '

# Pane borders
set -g pane-border-style fg=colour238
set -g pane-active-border-style fg=colour39

# Pane titles
set -g pane-border-status top
set -g pane-border-format '#{?pane_active,#[fg=colour39],#[fg=colour246]} #{pane_title} '

# Key bindings
bind r source-file ~/.tmux.conf \\; display-message "Config reloaded!"
bind | split-window -h
bind - split-window -v
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Enable vi mode
setw -g mode-keys vi
"""
        
        with open(self.tmux_config, 'w') as f:
            f.write(config)
            
    def check_warp_installed(self):
        """Check if Warp is installed"""
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to return exists application process "Warp"'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and result.stdout.strip() == "true"
        except:
            return False
            
    def launch_split_view(self):
        """Launch cable tester in split view"""
        self.create_tmux_config("split")
        
        applescript = f"""
tell application "Warp"
    activate
    
    -- Create new window
    tell application "System Events"
        keystroke "n" using {{command down}}
        delay 1
        
        -- Navigate to cable tester directory
        keystroke "cd {self.base_dir}"
        keystroke return
        delay 0.5
        
        -- Create tmux session with split panes
        keystroke "tmux -f {self.tmux_config} new-session -s cable_tester -n 'Main' -d"
        keystroke return
        delay 0.5
        
        -- Create horizontal split
        keystroke "tmux split-window -h -p 50 -t cable_tester"
        keystroke return
        delay 0.5
        
        -- Create bottom pane for logs
        keystroke "tmux split-window -v -p 30 -t cable_tester:0.0"
        keystroke return
        delay 0.5
        
        -- Setup backend in left pane
        keystroke "tmux send-keys -t cable_tester:0.0 'source venv/bin/activate' C-m"
        keystroke return
        keystroke "tmux send-keys -t cable_tester:0.0 'clear' C-m"
        keystroke return
        keystroke "tmux send-keys -t cable_tester:0.0 'echo \"=== Backend Server ===\"' C-m"
        keystroke return
        keystroke "tmux send-keys -t cable_tester:0.0 'python src/backend_server_logged.py' C-m"
        keystroke return
        
        -- Setup frontend in right pane
        keystroke "tmux send-keys -t cable_tester:0.1 'source venv/bin/activate' C-m"
        keystroke return
        keystroke "tmux send-keys -t cable_tester:0.1 'clear' C-m"
        keystroke return
        keystroke "tmux send-keys -t cable_tester:0.1 'echo \"=== Frontend Console ===\"' C-m"
        keystroke return
        keystroke "tmux send-keys -t cable_tester:0.1 'echo \"Waiting for backend...\"' C-m"
        keystroke return
        keystroke "tmux send-keys -t cable_tester:0.1 'sleep 3' C-m"
        keystroke return
        keystroke "tmux send-keys -t cable_tester:0.1 'python src/frontend_simple_fixed.py' C-m"
        keystroke return
        
        -- Setup log viewer in bottom pane
        keystroke "tmux send-keys -t cable_tester:0.2 'tail -f logs/backend_all.log' C-m"
        keystroke return
        
        -- Set pane titles
        keystroke "tmux select-pane -t cable_tester:0.0 -T 'Backend Server'"
        keystroke return
        keystroke "tmux select-pane -t cable_tester:0.1 -T 'Frontend Console'"
        keystroke return
        keystroke "tmux select-pane -t cable_tester:0.2 -T 'Live Logs'"
        keystroke return
        
        -- Attach to session
        keystroke "tmux attach -t cable_tester"
        keystroke return
    end tell
end tell
"""
        
        subprocess.run(["osascript", "-e", applescript])
        
    def launch_tabs_view(self):
        """Launch cable tester with separate tabs"""
        self.create_tmux_config("tabs")
        
        applescript = f"""
tell application "Warp"
    activate
    
    -- Create new window
    tell application "System Events"
        keystroke "n" using {{command down}}
        delay 1
        
        -- Navigate to cable tester directory
        keystroke "cd {self.base_dir}"
        keystroke return
        delay 0.5
        
        -- Create tmux session with multiple windows
        keystroke "tmux -f {self.tmux_config} new-session -s cable_tester -n 'Backend' -d"
        keystroke return
        delay 0.5
        
        -- Create frontend window
        keystroke "tmux new-window -t cable_tester -n 'Frontend'"
        keystroke return
        
        -- Create logs window
        keystroke "tmux new-window -t cable_tester -n 'Logs'"
        keystroke return
        
        -- Setup backend
        keystroke "tmux send-keys -t cable_tester:Backend 'source venv/bin/activate && python src/backend_server_logged.py' C-m"
        keystroke return
        
        -- Setup frontend
        keystroke "tmux send-keys -t cable_tester:Frontend 'source venv/bin/activate && sleep 3 && python src/frontend_simple_fixed.py' C-m"
        keystroke return
        
        -- Setup log viewer
        keystroke "tmux send-keys -t cable_tester:Logs 'tail -f logs/backend_all.log' C-m"
        keystroke return
        
        -- Switch to frontend window
        keystroke "tmux select-window -t cable_tester:Frontend"
        keystroke return
        
        -- Attach to session
        keystroke "tmux attach -t cable_tester"
        keystroke return
    end tell
end tell
"""
        
        subprocess.run(["osascript", "-e", applescript])
        
    def launch_monitoring_view(self):
        """Launch with monitoring dashboard"""
        self.create_tmux_config("monitor")
        
        # Create monitoring script
        monitor_script = self.base_dir / "monitor_dashboard.sh"
        monitor_content = """#!/bin/bash
while true; do
    clear
    echo "=== Cable Tester Monitoring Dashboard ==="
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Check backend status
    if pgrep -f "backend_server_logged.py" > /dev/null; then
        echo "Backend: ✅ RUNNING"
    else
        echo "Backend: ❌ STOPPED"
    fi
    
    # Check frontend status
    if pgrep -f "frontend_simple_fixed.py" > /dev/null; then
        echo "Frontend: ✅ RUNNING"
    else
        echo "Frontend: ❌ STOPPED"
    fi
    
    echo ""
    echo "=== Recent Logs ==="
    tail -n 5 logs/backend_all.log 2>/dev/null || echo "No logs yet"
    
    echo ""
    echo "=== Security Events ==="
    tail -n 3 logs/security_events.log 2>/dev/null || echo "No security events"
    
    sleep 2
done
"""
        
        with open(monitor_script, 'w') as f:
            f.write(monitor_content)
        monitor_script.chmod(0o755)
        
        applescript = f"""
tell application "Warp"
    activate
    
    -- Create new window
    tell application "System Events"
        keystroke "n" using {{command down}}
        delay 1
        
        -- Navigate to cable tester directory
        keystroke "cd {self.base_dir}"
        keystroke return
        delay 0.5
        
        -- Create tmux session with monitoring layout
        keystroke "tmux -f {self.tmux_config} new-session -s cable_monitor -n 'Monitor' -d"
        keystroke return
        
        -- Create 4-pane layout
        keystroke "tmux split-window -h -p 50"
        keystroke return
        keystroke "tmux split-window -v -p 50 -t 0"
        keystroke return
        keystroke "tmux split-window -v -p 50 -t 2"
        keystroke return
        
        -- Pane 0: Backend
        keystroke "tmux send-keys -t 0 'source venv/bin/activate && python src/backend_server_logged.py' C-m"
        keystroke return
        
        -- Pane 1: Frontend
        keystroke "tmux send-keys -t 1 'source venv/bin/activate && sleep 3 && python src/frontend_simple_fixed.py' C-m"
        keystroke return
        
        -- Pane 2: Monitoring dashboard
        keystroke "tmux send-keys -t 2 './monitor_dashboard.sh' C-m"
        keystroke return
        
        -- Pane 3: Live logs
        keystroke "tmux send-keys -t 3 'tail -f logs/*.log' C-m"
        keystroke return
        
        -- Set titles
        keystroke "tmux select-pane -t 0 -T 'Backend'"
        keystroke return
        keystroke "tmux select-pane -t 1 -T 'Frontend'"
        keystroke return
        keystroke "tmux select-pane -t 2 -T 'Monitor'"
        keystroke return
        keystroke "tmux select-pane -t 3 -T 'All Logs'"
        keystroke return
        
        -- Attach to session
        keystroke "tmux attach -t cable_monitor"
        keystroke return
    end tell
end tell
"""
        
        subprocess.run(["osascript", "-e", applescript])
        
    def kill_sessions(self):
        """Kill all cable tester tmux sessions"""
        sessions = ["cable_tester", "cable_monitor", "cable_backend", "cable_frontend"]
        for session in sessions:
            subprocess.run(["tmux", "kill-session", "-t", session], 
                         stderr=subprocess.DEVNULL)
        print("All cable tester sessions terminated")

def main():
    parser = argparse.ArgumentParser(description='Launch Cable Tester in Warp Terminal')
    parser.add_argument('layout', 
                       choices=['split', 'tabs', 'monitor', 'kill'],
                       help='Layout type or kill all sessions')
    
    args = parser.parse_args()
    
    launcher = WarpLauncher()
    
    # Check prerequisites
    if args.layout != 'kill':
        if not launcher.check_warp_installed():
            print("Error: Warp terminal is not installed")
            print("Install from: https://www.warp.dev")
            sys.exit(1)
            
        if not (launcher.base_dir / "venv").exists():
            print("Error: Virtual environment not found")
            print("Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
            sys.exit(1)
    
    # Launch requested layout
    if args.layout == 'split':
        print("Launching Cable Tester in split view...")
        launcher.launch_split_view()
    elif args.layout == 'tabs':
        print("Launching Cable Tester with tabs...")
        launcher.launch_tabs_view()
    elif args.layout == 'monitor':
        print("Launching Cable Tester with monitoring dashboard...")
        launcher.launch_monitoring_view()
    elif args.layout == 'kill':
        launcher.kill_sessions()
        
    if args.layout != 'kill':
        print("\nTmux controls:")
        print("  - Switch panes: Ctrl+B then arrow keys")
        print("  - Switch windows: Ctrl+B then n/p")
        print("  - Detach: Ctrl+B then d")
        print("  - Kill session: Ctrl+B then :kill-session")

if __name__ == '__main__':
    main()