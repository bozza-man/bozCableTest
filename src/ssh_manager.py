#!/usr/bin/env python3

import paramiko
import socket
import time
import json
import re
from typing import Dict, Optional, Tuple
from pathlib import Path

class SSHManager:
    def __init__(self):
        self.ssh_client = None
        self.sftp_client = None
        self.remote_host = None
        self.remote_user = None
        self.connected = False
        
    def connect(self, host: str, username: str, password: Optional[str] = None, 
                key_path: Optional[str] = None, port: int = 22) -> bool:
        """Establish SSH connection to remote Mac"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': host,
                'port': port,
                'username': username,
                'timeout': 30
            }
            
            if password:
                connect_kwargs['password'] = password
            elif key_path:
                connect_kwargs['key_filename'] = key_path
            else:
                # Try system SSH keys
                ssh_dir = Path.home() / '.ssh'
                possible_keys = ['id_rsa', 'id_ed25519', 'id_ecdsa']
                for key in possible_keys:
                    key_file = ssh_dir / key
                    if key_file.exists():
                        connect_kwargs['key_filename'] = str(key_file)
                        break
            
            self.ssh_client.connect(**connect_kwargs)
            self.sftp_client = self.ssh_client.open_sftp()
            self.remote_host = host
            self.remote_user = username
            self.connected = True
            
            # Verify connection and macOS
            if not self._verify_macos():
                raise Exception("Remote system is not macOS")
                
            return True
            
        except Exception as e:
            print(f"SSH connection failed: {e}")
            self.disconnect()
            return False
    
    def _verify_macos(self) -> bool:
        """Verify remote system is macOS"""
        stdout, stderr, returncode = self.execute_command("uname -s")
        return stdout.strip() == "Darwin" if returncode == 0 else False
    
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """Execute command on remote Mac"""
        if not self.connected:
            return "", "Not connected", -1
            
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            return stdout_data, stderr_data, stdout.channel.recv_exit_status()
        except Exception as e:
            return "", str(e), -1
    
    def deploy_agent(self) -> bool:
        """Deploy testing agent to remote Mac"""
        if not self.connected:
            return False
            
        try:
            # Create remote directory
            self.execute_command("mkdir -p ~/cable_tester_agent")
            
            # Copy agent files
            agent_files = [
                'remote_agent.py',
                'usb_monitor.py',
                'performance_tester.py'
            ]
            
            for file in agent_files:
                local_path = Path(__file__).parent / file
                if local_path.exists():
                    remote_path = f"~/cable_tester_agent/{file}"
                    self.sftp_client.put(str(local_path), remote_path)
            
            # Make executable
            self.execute_command("chmod +x ~/cable_tester_agent/*.py")
            
            # Install dependencies if needed
            self.execute_command("cd ~/cable_tester_agent && pip3 install paramiko psutil")
            
            return True
            
        except Exception as e:
            print(f"Failed to deploy agent: {e}")
            return False
    
    def start_remote_agent(self) -> bool:
        """Start the remote testing agent"""
        if not self.connected:
            return False
            
        # Start agent in background
        stdout, stderr, returncode = self.execute_command(
            "cd ~/cable_tester_agent && nohup python3 remote_agent.py > agent.log 2>&1 & echo $!"
        )
        
        if returncode == 0:
            agent_pid = stdout.strip()
            print(f"Remote agent started with PID: {agent_pid}")
            return True
        
        return False
    
    def stop_remote_agent(self) -> bool:
        """Stop the remote testing agent"""
        if not self.connected:
            return False
            
        # Find and kill agent process
        stdout, stderr, returncode = self.execute_command(
            "ps aux | grep 'remote_agent.py' | grep -v grep | awk '{print $2}' | xargs kill -9"
        )
        
        return returncode == 0
    
    def get_remote_usb_devices(self) -> Optional[Dict]:
        """Get USB devices from remote Mac"""
        if not self.connected:
            return None
            
        stdout, stderr, returncode = self.execute_command(
            "system_profiler SPUSBDataType -json"
        )
        
        if returncode == 0:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return None
        
        return None
    
    def transfer_file(self, local_path: str, remote_path: str, 
                     direction: str = 'put') -> bool:
        """Transfer file between local and remote Mac"""
        if not self.connected:
            return False
            
        try:
            if direction == 'put':
                self.sftp_client.put(local_path, remote_path)
            else:  # get
                self.sftp_client.get(remote_path, local_path)
            return True
        except Exception as e:
            print(f"File transfer failed: {e}")
            return False
    
    def create_test_file(self, size_mb: int) -> str:
        """Create test file on remote Mac for transfer testing"""
        if not self.connected:
            return ""
            
        remote_path = f"~/cable_tester_agent/test_file_{size_mb}MB.dat"
        
        # Create file with random data
        stdout, stderr, returncode = self.execute_command(
            f"dd if=/dev/urandom of={remote_path} bs=1M count={size_mb}"
        )
        
        return remote_path if returncode == 0 else ""
    
    def check_thunderbolt_status(self) -> Optional[Dict]:
        """Check Thunderbolt status on remote Mac"""
        if not self.connected:
            return None
            
        # Get Thunderbolt info
        stdout, stderr, returncode = self.execute_command(
            "system_profiler SPThunderboltDataType -json"
        )
        
        if returncode == 0:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return None
        
        return None
    
    def monitor_power_delivery(self) -> Optional[Dict]:
        """Monitor USB Power Delivery on remote Mac"""
        if not self.connected:
            return None
            
        # Use ioreg to get power info
        stdout, stderr, returncode = self.execute_command(
            "ioreg -r -c AppleUSBHostPort -l | grep -E '(PortCurrentAllocation|PortPowerState)'"
        )
        
        if returncode == 0:
            power_info = {}
            lines = stdout.strip().split('\n')
            for line in lines:
                if 'PortCurrentAllocation' in line:
                    match = re.search(r'= (\d+)', line)
                    if match:
                        power_info['current_ma'] = int(match.group(1))
                elif 'PortPowerState' in line:
                    match = re.search(r'= (\d+)', line)
                    if match:
                        power_info['power_state'] = int(match.group(1))
            
            return power_info
        
        return None
    
    def disconnect(self):
        """Close SSH connection"""
        if self.sftp_client:
            self.sftp_client.close()
            self.sftp_client = None
            
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
            
        self.connected = False
        self.remote_host = None
        self.remote_user = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()