#!/usr/bin/env python3

import subprocess
import sys

def create_remote_pane(host="192.168.1.100", username="testuser"):
    """Create a third tmux pane for remote SSH connection"""
    
    try:
        # Check if we're in tmux
        current_session = subprocess.check_output(
            ['tmux', 'display-message', '-p', '#S'], 
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        if not current_session:
            print("Not in a tmux session")
            return False
            
        # Check current number of panes
        pane_count = int(subprocess.check_output(
            ['tmux', 'list-panes', '-t', current_session, '-F', '#{window_panes}'],
            stderr=subprocess.DEVNULL
        ).decode().strip().split('\n')[0])
        
        # Only create third pane if we have 2 or fewer
        if pane_count < 3:
            print(f"\n[INFO] Creating remote SSH pane for {username}@{host}...")
            
            # Create vertical split
            subprocess.run(['tmux', 'split-window', '-h', '-p', '33', '-t', current_session])
            
            # Set pane title
            subprocess.run(['tmux', 'select-pane', '-t', '{right}', '-T', f'Remote: {host}'])
            
            # Clear and set up the pane
            subprocess.run(['tmux', 'send-keys', '-t', '{right}', 'clear', 'C-m'])
            subprocess.run(['tmux', 'send-keys', '-t', '{right}', f"echo '=== Remote SSH Connection ==='", 'C-m'])
            subprocess.run(['tmux', 'send-keys', '-t', '{right}', f"echo 'Connecting to {username}@{host}...'", 'C-m'])
            subprocess.run(['tmux', 'send-keys', '-t', '{right}', f"ssh {username}@{host}", 'C-m'])
            
            # Return focus to frontend pane
            subprocess.run(['tmux', 'select-pane', '-t', '.1'])
            
            print(f"[INFO] Remote pane created. Check the right side of your window.")
            return True
        else:
            print("[INFO] Remote pane already exists")
            return False
            
    except subprocess.CalledProcessError:
        print("[WARN] Could not create remote pane (tmux error)")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    # Can be called with arguments: python trigger_remote_pane.py host username
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
    username = sys.argv[2] if len(sys.argv) > 2 else "testuser"
    create_remote_pane(host, username)