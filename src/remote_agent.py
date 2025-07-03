#!/usr/bin/env python3

import socket
import json
import subprocess
import threading
import time
import sys
import re
from datetime import datetime

class RemoteAgent:
    def __init__(self, port: int = 9999):
        self.port = port
        self.server_socket = None
        self.running = False
        self.client_connections = []
        
    def start(self):
        """Start the remote agent server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"Remote agent listening on port {self.port}")
        
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Connection from {address}")
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}")
    
    def handle_client(self, client_socket):
        """Handle individual client connections"""
        try:
            while self.running:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                try:
                    request = json.loads(data)
                    response = self.process_request(request)
                    client_socket.send(json.dumps(response).encode('utf-8'))
                except json.JSONDecodeError:
                    error_response = {
                        'status': 'error',
                        'message': 'Invalid JSON'
                    }
                    client_socket.send(json.dumps(error_response).encode('utf-8'))
                    
        except Exception as e:
            print(f"Client handler error: {e}")
        finally:
            client_socket.close()
    
    def process_request(self, request: dict) -> dict:
        """Process incoming requests"""
        command = request.get('command')
        
        if command == 'get_usb_devices':
            return self.get_usb_devices()
        
        elif command == 'get_thunderbolt_info':
            return self.get_thunderbolt_info()
        
        elif command == 'monitor_usb_changes':
            duration = request.get('duration', 10)
            return self.monitor_usb_changes(duration)
        
        elif command == 'get_power_info':
            return self.get_power_info()
        
        elif command == 'test_data_transfer':
            return self.test_data_transfer(request.get('size_mb', 10))
        
        elif command == 'get_system_info':
            return self.get_system_info()
        
        else:
            return {
                'status': 'error',
                'message': f'Unknown command: {command}'
            }
    
    def get_usb_devices(self) -> dict:
        """Get current USB devices"""
        try:
            result = subprocess.run(
                ['system_profiler', 'SPUSBDataType', '-json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'data': json.loads(result.stdout),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_thunderbolt_info(self) -> dict:
        """Get Thunderbolt information"""
        try:
            result = subprocess.run(
                ['system_profiler', 'SPThunderboltDataType', '-json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'data': json.loads(result.stdout),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def monitor_usb_changes(self, duration: int) -> dict:
        """Monitor USB changes for specified duration"""
        start_time = time.time()
        initial_devices = self.get_usb_devices()
        changes = []
        
        while time.time() - start_time < duration:
            current_devices = self.get_usb_devices()
            
            if current_devices != initial_devices:
                changes.append({
                    'timestamp': datetime.now().isoformat(),
                    'devices': current_devices
                })
                initial_devices = current_devices
            
            time.sleep(0.5)
        
        return {
            'status': 'success',
            'changes': changes,
            'duration': duration
        }
    
    def get_power_info(self) -> dict:
        """Get USB power information"""
        try:
            # Get power info from ioreg
            result = subprocess.run(
                ['ioreg', '-r', '-c', 'AppleUSBHostPort', '-l'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                power_data = []
                lines = result.stdout.split('\n')
                
                current_port = {}
                for line in lines:
                    if 'PortCurrentAllocation' in line:
                        match = re.search(r'= (\d+)', line)
                        if match:
                            current_port['current_ma'] = int(match.group(1))
                    elif 'PortPowerState' in line:
                        match = re.search(r'= (\d+)', line)
                        if match:
                            current_port['power_state'] = int(match.group(1))
                    elif 'USB Port' in line and current_port:
                        power_data.append(current_port)
                        current_port = {}
                
                return {
                    'status': 'success',
                    'power_data': power_data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def test_data_transfer(self, size_mb: int) -> dict:
        """Create test file for data transfer testing"""
        try:
            test_file = f'/tmp/cable_test_{size_mb}MB.dat'
            
            # Create test file
            result = subprocess.run(
                ['dd', 'if=/dev/urandom', f'of={test_file}', 
                 'bs=1M', f'count={size_mb}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Calculate checksum
                checksum_result = subprocess.run(
                    ['shasum', '-a', '256', test_file],
                    capture_output=True,
                    text=True
                )
                
                checksum = checksum_result.stdout.split()[0] if checksum_result.returncode == 0 else ''
                
                return {
                    'status': 'success',
                    'file_path': test_file,
                    'size_mb': size_mb,
                    'checksum': checksum
                }
            else:
                return {
                    'status': 'error',
                    'message': result.stderr
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_system_info(self) -> dict:
        """Get system information"""
        try:
            # Get macOS version
            version_result = subprocess.run(
                ['sw_vers'],
                capture_output=True,
                text=True
            )
            
            # Get hardware info
            hw_result = subprocess.run(
                ['system_profiler', 'SPHardwareDataType', '-json'],
                capture_output=True,
                text=True
            )
            
            return {
                'status': 'success',
                'os_info': version_result.stdout if version_result.returncode == 0 else '',
                'hardware': json.loads(hw_result.stdout) if hw_result.returncode == 0 else {},
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def stop(self):
        """Stop the remote agent"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

if __name__ == "__main__":
    agent = RemoteAgent()
    try:
        agent.start()
    except KeyboardInterrupt:
        print("\nShutting down remote agent...")
        agent.stop()
        sys.exit(0)