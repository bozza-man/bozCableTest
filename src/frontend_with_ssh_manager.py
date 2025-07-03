#!/usr/bin/env python3

import asyncio
import websockets
import json
import sys
import threading
import subprocess
from datetime import datetime
import getpass
from typing import Dict, Optional
import queue
from ssh_server_manager import SSHServerManager

class EnhancedFrontend:
    def __init__(self):
        self.websocket = None
        self.connected = False
        self.running = True
        self.input_queue = queue.Queue()
        self.ssh_manager = SSHServerManager()
        self.waiting_for_input = None
        self.input_mode = None
        
    async def connect_to_backend(self, uri='ws://localhost:8765'):
        """Connect to backend WebSocket server"""
        try:
            self.websocket = await websockets.connect(uri)
            self.connected = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to backend server")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to connect: {e}")
            return False
            
    def handle_message(self, data: Dict):
        """Handle message from backend"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        msg_type = data.get('type')
        
        if msg_type == 'status':
            print(f"[{timestamp}] {data.get('message', '')}")
            
        elif msg_type == 'ssh_status':
            if data.get('connected'):
                print(f"[{timestamp}] ✅ SSH connected to {data.get('host')}")
                # Create third pane for SSH
                self._create_ssh_pane(data.get('host'))
            else:
                print(f"[{timestamp}] ❌ SSH connection failed")
                
        elif msg_type == 'error':
            print(f"[{timestamp}] ERROR: {data.get('message', 'Unknown error')}")
            
        elif msg_type == 'test_results':
            test_name = data.get('test', 'unknown')
            results = data.get('results', {})
            print(f"\n[{timestamp}] === {test_name.upper()} TEST RESULTS ===")
            
            if test_name == 'security':
                print(f"Devices tested: {results.get('devices_tested', 0)}")
                print(f"Safe: {'✅ Yes' if results.get('is_safe') else '❌ No'}")
                threats = results.get('threats_found', [])
                if threats:
                    print("Threats found:")
                    for threat in threats:
                        print(f"  - {threat}")
                        
            elif test_name == 'performance':
                print(f"USB 3.0 Speed: {results.get('usb3_speed', 'N/A')}")
                print(f"Thunderbolt Speed: {results.get('thunderbolt_speed', 'N/A')}")
                print(f"Power Delivery: {results.get('power_delivery', 'N/A')}")
                
            print("=" * 40)
            
        elif msg_type == 'security_alert':
            threats = data.get('threats', [])
            print(f"\n[{timestamp}] 🚨 SECURITY ALERT 🚨")
            for threat in threats:
                print(f"  ⚠️  {threat}")
            print("")
            
        elif msg_type == 'status_response':
            status = data.get('status', {})
            print(f"\n[{timestamp}] === SYSTEM STATUS ===")
            print(f"Backend: {'✅ Running' if status.get('backend_running') else '❌ Stopped'}")
            print(f"SSH: {'✅ Connected to ' + status.get('ssh_host', '') if status.get('ssh_connected') else '❌ Not connected'}")
            print(f"Test in progress: {'Yes' if status.get('test_in_progress') else 'No'}")
            print(f"USB devices: {status.get('usb_devices', 0)}")
            print(f"Monitoring: {'✅ Active' if status.get('monitoring_active') else '❌ Inactive'}")
            
            sec_status = status.get('security_status', {})
            if sec_status.get('lockdown_mode'):
                print(f"⚠️  LOCKDOWN MODE ACTIVE")
            print("=" * 40)
            
        elif msg_type == 'emergency_stop_complete':
            print(f"\n[{timestamp}] 🛑 EMERGENCY STOP COMPLETE")
            print("All monitoring has been stopped.")
            print("System is in safe mode.")
            
        elif msg_type == 'usb_event':
            event = data.get('event', 'unknown')
            device = data.get('device', {})
            print(f"[{timestamp}] USB: {event} - {device.get('name', 'Unknown device')}")
            
        elif msg_type == 'connection':
            print(f"[{timestamp}] Connected to backend v{data.get('backend_version', 'unknown')}")
            
    async def listen_for_messages(self):
        """Listen for messages from backend"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            print("\n[ERROR] Connection to backend lost")
            
    def _create_ssh_pane(self, host):
        """Create third pane for SSH connection"""
        try:
            # Check if we're in tmux
            current_session = subprocess.check_output(
                ['tmux', 'display-message', '-p', '#S'], 
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            if current_session:
                # Check pane count
                pane_count = int(subprocess.check_output(
                    ['tmux', 'list-panes', '-F', '#{window_panes}'],
                    stderr=subprocess.DEVNULL
                ).decode().strip().split('\n')[0])
                
                if pane_count < 3:
                    # Create vertical split
                    subprocess.run(['tmux', 'split-window', '-h', '-p', '33'])
                    subprocess.run(['tmux', 'select-pane', '-t', '{right}', '-T', f'Remote: {host}'])
                    
                    # Get current server details
                    server = self.ssh_manager.get_current_server()
                    if server:
                        ssh_cmd = f"ssh -p {server['port']} {server['username']}@{server['host']}"
                        if server.get('key_path'):
                            ssh_cmd = f"ssh -i {server['key_path']} -p {server['port']} {server['username']}@{server['host']}"
                        
                        subprocess.run(['tmux', 'send-keys', '-t', '{right}', ssh_cmd, 'C-m'])
                    
                    # Return focus to frontend
                    subprocess.run(['tmux', 'select-pane', '-t', '.1'])
                    
        except subprocess.CalledProcessError:
            pass
            
    def show_ssh_menu(self):
        """Show SSH server management menu"""
        print("\n=== SSH Server Management ===")
        
        # Show current server
        current = self.ssh_manager.get_current_server()
        if current:
            print(f"\nCurrently selected: {current['name']} ({current['username']}@{current['host']})")
        else:
            print("\nNo server selected")
            
        # List all servers
        servers = self.ssh_manager.list_servers()
        if servers:
            print("\nSaved servers:")
            for i, server in enumerate(servers, 1):
                marker = "→" if server['current'] else " "
                print(f"{marker} {i}. {server['name']} - {server['username']}@{server['host']}:{server['port']}")
        else:
            print("\nNo saved servers")
            
        print("\nOptions:")
        print("  a - Add new server")
        print("  s - Select server (by number)")
        print("  r - Remove server")
        print("  c - Connect to current server")
        print("  b - Back to main menu")
        print("\nChoice: ", end='', flush=True)
        
        self.input_mode = 'ssh_menu'
        
    def add_server_flow(self):
        """Interactive flow to add a new server"""
        print("\n=== Add New SSH Server ===")
        self.input_mode = 'add_server_name'
        print("Server name (e.g., 'Test Mac', 'Production'): ", end='', flush=True)
        
    async def handle_ssh_menu_input(self, choice):
        """Handle SSH menu choices"""
        if choice == 'a':
            self.add_server_flow()
        elif choice == 's':
            servers = self.ssh_manager.list_servers()
            if servers:
                print("Enter server number: ", end='', flush=True)
                self.input_mode = 'select_server'
            else:
                print("No servers to select")
                self.show_menu()
        elif choice == 'r':
            servers = self.ssh_manager.list_servers()
            if servers:
                print("Enter server number to remove: ", end='', flush=True)
                self.input_mode = 'remove_server'
            else:
                print("No servers to remove")
                self.show_menu()
        elif choice == 'c':
            server = self.ssh_manager.get_current_server()
            if server:
                await self.connect_to_server(server)
            else:
                print("No server selected")
                self.show_menu()
        elif choice == 'b':
            self.show_menu()
        else:
            print("Invalid choice")
            self.show_ssh_menu()
            
    async def connect_to_server(self, server):
        """Connect to a specific SSH server"""
        print(f"\nConnecting to {server['name']} ({server['username']}@{server['host']})...")
        
        cmd = {
            'type': 'connect_ssh',
            'host': server['host'],
            'username': server['username'],
            'port': server['port']
        }
        
        # Add password or key
        if server.get('key_path'):
            cmd['key_path'] = server['key_path']
        else:
            # For demo, using empty password - in real use, would prompt
            cmd['password'] = ''
            
        await self.send_command(cmd)
        self.show_menu()
        
    async def send_command(self, command: Dict):
        """Send command to backend"""
        if self.websocket and self.connected:
            await self.websocket.send(json.dumps(command))
            
    def input_thread(self):
        """Thread to handle blocking input"""
        while self.running:
            try:
                user_input = input()
                self.input_queue.put(user_input)
            except EOFError:
                break
                
    async def process_input(self):
        """Process input from queue"""
        # Variables for multi-step input
        new_server = {}
        
        while self.running and self.connected:
            try:
                user_input = self.input_queue.get_nowait()
                
                # Handle different input modes
                if self.input_mode == 'ssh_menu':
                    await self.handle_ssh_menu_input(user_input)
                    
                elif self.input_mode == 'add_server_name':
                    new_server['name'] = user_input
                    print("Host/IP address: ", end='', flush=True)
                    self.input_mode = 'add_server_host'
                    
                elif self.input_mode == 'add_server_host':
                    new_server['host'] = user_input
                    print("Username: ", end='', flush=True)
                    self.input_mode = 'add_server_username'
                    
                elif self.input_mode == 'add_server_username':
                    new_server['username'] = user_input
                    print("Port (22): ", end='', flush=True)
                    self.input_mode = 'add_server_port'
                    
                elif self.input_mode == 'add_server_port':
                    port = user_input.strip() or '22'
                    new_server['port'] = int(port)
                    print("SSH key path (leave empty for password auth): ", end='', flush=True)
                    self.input_mode = 'add_server_key'
                    
                elif self.input_mode == 'add_server_key':
                    key_path = user_input.strip() or None
                    
                    # Add the server
                    if self.ssh_manager.add_server(
                        new_server['name'],
                        new_server['host'],
                        new_server['username'],
                        new_server['port'],
                        key_path
                    ):
                        print(f"\n✅ Server '{new_server['name']}' added successfully")
                        self.ssh_manager.select_server(new_server['name'])
                    else:
                        print(f"\n❌ Server '{new_server['name']}' already exists")
                    
                    self.show_ssh_menu()
                    
                elif self.input_mode == 'select_server':
                    try:
                        idx = int(user_input) - 1
                        servers = self.ssh_manager.list_servers()
                        if 0 <= idx < len(servers):
                            server_name = servers[idx]['name']
                            self.ssh_manager.select_server(server_name)
                            print(f"\n✅ Selected: {server_name}")
                        else:
                            print("Invalid number")
                    except ValueError:
                        print("Invalid input")
                    self.show_ssh_menu()
                    
                elif self.input_mode == 'remove_server':
                    try:
                        idx = int(user_input) - 1
                        servers = self.ssh_manager.list_servers()
                        if 0 <= idx < len(servers):
                            server_name = servers[idx]['name']
                            self.ssh_manager.remove_server(server_name)
                            print(f"\n✅ Removed: {server_name}")
                        else:
                            print("Invalid number")
                    except ValueError:
                        print("Invalid input")
                    self.show_ssh_menu()
                    
                else:  # Main menu
                    if user_input == 'q':
                        self.running = False
                    elif user_input == '1':
                        self.show_ssh_menu()
                    elif user_input == '2':
                        print("\nStarting security test...")
                        await self.send_command({'type': 'start_security_test'})
                    elif user_input == '3':
                        print("\nStarting performance tests...")
                        await self.send_command({'type': 'start_performance_test'})
                    elif user_input == '4':
                        await self.send_command({'type': 'get_status'})
                    elif user_input == '5':
                        print("\n🚨 EMERGENCY STOP 🚨")
                        await self.send_command({'type': 'emergency_stop'})
                    elif user_input == 'h' or user_input == 'help':
                        self.show_help()
                    elif user_input == 'logs':
                        self.show_recent_logs()
                    else:
                        print("Invalid command. Enter 1-5, 'h' for help, or 'q' to quit.")
                        
            except queue.Empty:
                await asyncio.sleep(0.1)
                
    def show_help(self):
        """Show detailed help information"""
        print("\n=== Cable Tester Help ===")
        print("\n🛡️  SECURITY FEATURES:")
        print("  • Detects HAK5 Rubber Ducky, Bash Bunny, and other malicious cables")
        print("  • Monitors for rapid enumeration attacks")
        print("  • Detects HID flooding and DMA attempts")
        print("  • Automatic lockdown mode for critical threats")
        print("  • Comprehensive logging of all security events")
        
        print("\n🔌 CABLE TESTING:")
        print("  • USB-C and Thunderbolt cable verification")
        print("  • Two-Mac setup with SSH connection")
        print("  • Real-time monitoring of USB bus changes")
        print("  • Performance testing (USB 3.0, Thunderbolt, Power Delivery)")
        
        print("\n💻 TMUX COMMANDS:")
        print("  • View backend:  tmux select-pane -t cable_enhanced:0.0")
        print("  • View frontend: tmux select-pane -t cable_enhanced:0.1")
        print("  • Detach:        Ctrl+B, then D")
        print("  • Reattach:      tmux attach -t cable_enhanced")
        
        print("\n🔍 TROUBLESHOOTING:")
        print("  • Check backend:  tail -f logs/backend_all.log")
        print("  • Check errors:   tail -f logs/backend_errors.log")
        print("  • Check security: tail -f logs/security_events.log")
        print("  • Kill backend:   pkill -f backend_server_logged.py")
        
        print("\nPress Enter to return to menu...", end='', flush=True)
        input()
        self.show_menu()
        
    def show_recent_logs(self):
        """Show recent log entries"""
        import subprocess
        print("\n=== Recent Log Activity ===")
        
        try:
            # Show last 10 lines of backend log
            print("\n📋 Recent Backend Activity:")
            result = subprocess.run(['tail', '-10', 'logs/backend_all.log'], 
                                  capture_output=True, text=True)
            print(result.stdout)
            
            # Show any recent errors
            print("\n⚠️  Recent Errors:")
            result = subprocess.run(['tail', '-5', 'logs/backend_errors.log'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                print(result.stdout)
            else:
                print("No recent errors")
                
            # Show any security events
            print("\n🛡️  Recent Security Events:")
            result = subprocess.run(['tail', '-5', 'logs/security_events.log'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                print(result.stdout)
            else:
                print("No recent security events")
                
        except Exception as e:
            print(f"Error reading logs: {e}")
            
        print("\nPress Enter to return to menu...", end='', flush=True)
        input()
        self.show_menu()
    
    def show_menu(self):
        """Show main command menu"""
        print("\n=== Cable Tester Frontend ===")
        
        # Show current SSH server if any
        current = self.ssh_manager.get_current_server()
        if current:
            print(f"SSH Server: {current['name']} ({current['username']}@{current['host']})")
        
        print("\n🔧 Testing Commands:")
        print("  1 - SSH Server Management")
        print("  2 - Run security test (scan for malicious cables)")
        print("  3 - Run performance tests (requires SSH)")
        print("  4 - Get system status")
        print("  5 - Emergency stop (lockdown USB)")
        print("  h - Show detailed help")
        print("  logs - View recent log activity")
        print("  q - Quit")
        
        print("\n📜 Available Scripts:")
        print("  • ./launch_enhanced.sh        - Launch in new Warp window")
        print("  • ./warp_manual_launch.sh     - Create session (manual attach)")
        print("  • ./restart_backend.sh        - Restart backend server")
        print("  • ./restart_frontend.sh       - Restart frontend")
        print("  • ./restart_all.sh            - Restart entire system")
        
        print("\n📁 Log Files:")
        print("  • logs/backend_all.log        - All backend activity")
        print("  • logs/backend_errors.log     - Errors only")
        print("  • logs/security_events.log    - Security alerts")
        print("  • logs/session_*.log          - Session-specific logs")
        
        print("\nEnter command (1-5, h, logs, q): ", end='', flush=True)
        self.input_mode = None
        
    async def main(self):
        """Main frontend loop"""
        if not await self.connect_to_backend():
            return
            
        self.show_menu()
        
        # Start input thread
        input_thread = threading.Thread(target=self.input_thread, daemon=True)
        input_thread.start()
        
        try:
            listen_task = asyncio.create_task(self.listen_for_messages())
            input_task = asyncio.create_task(self.process_input())
            await asyncio.gather(listen_task, input_task)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.running = False
            if self.websocket:
                await self.websocket.close()

def main():
    frontend = EnhancedFrontend()
    asyncio.run(frontend.main())

if __name__ == "__main__":
    main()