#!/usr/bin/env python3

import asyncio
import json
from ssh_manager import SSHManager
import subprocess
import time

class SSHVisualManager(SSHManager):
    """Extended SSH manager that creates visual pane for remote connection"""
    
    def __init__(self):
        super().__init__()
        self.remote_pane_created = False
        
    def connect_with_pane(self, host: str, username: str, password=None, key_path=None):
        """Connect to SSH and create a new tmux pane for remote monitoring"""
        
        # First establish the connection
        success = self.connect(host, username, password, key_path)
        
        if success and not self.remote_pane_created:
            # Create a new pane in the current tmux window
            self._create_remote_pane(host, username)
            self.remote_pane_created = True
            
        return success
    
    def _create_remote_pane(self, host: str, username: str):
        """Create a new tmux pane for remote SSH session"""
        try:
            # Check if we're in a tmux session
            tmux_session = subprocess.check_output(['tmux', 'display-message', '-p', '#S'], 
                                                 stderr=subprocess.DEVNULL).decode().strip()
            
            if tmux_session:
                # Create a vertical split (right pane) in the current window
                subprocess.run(['tmux', 'split-window', '-h', '-p', '33'])
                time.sleep(0.5)
                
                # Set the pane title
                subprocess.run(['tmux', 'select-pane', '-T', f'Remote: {host}'])
                
                # SSH into the remote host in the new pane
                ssh_cmd = f'ssh {username}@{host}'
                if self.remote_user and self.remote_host:
                    # If we have an active connection, use those details
                    ssh_cmd = f'ssh {self.remote_user}@{self.remote_host}'
                
                # Send the SSH command to the new pane
                subprocess.run(['tmux', 'send-keys', '-t', '{right}', ssh_cmd, 'C-m'])
                
                # After SSH connects, run the remote agent status check
                time.sleep(2)
                status_cmd = 'echo "=== Remote Mac Connected ==="; ps aux | grep cable_tester_agent | grep -v grep || echo "Remote agent not running yet"'
                subprocess.run(['tmux', 'send-keys', '-t', '{right}', status_cmd, 'C-m'])
                
        except subprocess.CalledProcessError:
            # Not in tmux or error creating pane
            print("Note: Could not create visual pane (not in tmux session)")
            
    def close_remote_pane(self):
        """Close the remote SSH pane"""
        if self.remote_pane_created:
            try:
                # Kill the rightmost pane
                subprocess.run(['tmux', 'kill-pane', '-t', '{right}'])
                self.remote_pane_created = False
            except:
                pass