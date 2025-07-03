#!/usr/bin/env python3
"""
Optimized Dynamic Terminal Frontend with SSH Manager Integration
Reduces flickering by only redrawing changed sections
"""

import asyncio
import websockets
import json
import sys
import os
import curses
from datetime import datetime
from collections import deque
import threading
import signal

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ssh_server_manager import SSHServerManager

class OptimizedDynamicSSHTerminalUI:
    def __init__(self):
        self.screen = None
        self.websocket = None
        self.running = True
        self.current_selection = 0
        self.menu_items = []
        self.connection_status = "Disconnected"
        self.alerts = deque(maxlen=5)
        self.ssh_connected = False
        self.remote_ip = None
        self.usb_devices = []
        self.security_status = "Idle"
        self.test_results = {}
        self.backend_connected = False
        self.lock = threading.Lock()
        self.ssh_manager = SSHServerManager()
        self.in_ssh_menu = False
        self.ssh_servers = []
        self.ssh_selection = 0
        
        # Track what needs redrawing
        self.needs_full_redraw = True
        self.needs_menu_redraw = False
        self.needs_status_redraw = False
        self.needs_alerts_redraw = False
        self.last_drawn_state = {}
        
    def init_menu(self):
        """Initialize menu items based on connection state"""
        old_menu_count = len(self.menu_items)
        
        if self.in_ssh_menu:
            # SSH server selection menu
            self.menu_items = []
            self.ssh_servers = self.ssh_manager.list_servers()
            
            for server in self.ssh_servers:
                self.menu_items.append((
                    f"{server['name']} ({server['host']})",
                    lambda s=server: self.connect_to_server(s)
                ))
                
            self.menu_items.extend([
                ("Add New Server", self.add_new_server),
                ("Back to Main Menu", self.back_to_main)
            ])
        else:
            # Main menu
            self.menu_items = [
                ("Connect to Backend", self.connect_backend),
                ("SSH Server Management", self.open_ssh_menu),
                ("Run Security Test", self.run_security_test),
                ("Run Performance Test", self.run_performance_test),
                ("View Test Results", self.view_results),
                ("Clear Alerts", self.clear_alerts),
                ("Exit", self.exit_app)
            ]
        
        # Only trigger redraw if menu actually changed
        if old_menu_count != len(self.menu_items):
            self.needs_menu_redraw = True
            
    def add_alert(self, message, level="INFO"):
        """Add alert to the alerts queue"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        with self.lock:
            self.alerts.append(f"[{timestamp}] {level}: {message}")
            self.needs_alerts_redraw = True
            
    def draw_header(self):
        """Draw the header section"""
        try:
            height, width = self.screen.getmaxyx()
            header = "🔌 USB-C/Thunderbolt Cable Tester 🔌"
            header_line = 0
            
            # Clear the header area
            self.screen.move(header_line, 0)
            self.screen.clrtoeol()
            self.screen.move(header_line + 1, 0)
            self.screen.clrtoeol()
            
            # Draw header
            self.screen.addstr(header_line, (width - len(header)) // 2, header, 
                             curses.A_BOLD | curses.color_pair(1))
            self.screen.addstr(header_line + 1, 0, "─" * width, curses.color_pair(2))
        except:
            pass
            
    def draw_menu(self):
        """Draw the interactive menu"""
        if not self.needs_menu_redraw and not self.needs_full_redraw:
            return
            
        try:
            height, width = self.screen.getmaxyx()
            menu_start_y = 3
            
            # Clear menu area
            max_menu_height = len(self.menu_items) + 3
            for y in range(menu_start_y, min(menu_start_y + max_menu_height, height - 10)):
                self.screen.move(y, 0)
                self.screen.clrtoeol()
            
            title = "SSH Servers:" if self.in_ssh_menu else "Main Menu:"
            self.screen.addstr(menu_start_y, 2, title, curses.A_BOLD)
            
            for idx, (item_text, _) in enumerate(self.menu_items):
                y = menu_start_y + 2 + idx
                if y >= height - 10:
                    break
                    
                # Disable certain options based on state
                disabled = False
                if not self.in_ssh_menu:
                    if not self.backend_connected and item_text not in ["Connect to Backend", "Exit"]:
                        disabled = True
                    elif not self.ssh_connected and item_text in ["Run Security Test", "Run Performance Test"]:
                        disabled = True
                    
                if idx == self.current_selection:
                    attr = curses.A_REVERSE
                else:
                    attr = curses.A_DIM if disabled else curses.A_NORMAL
                    
                prefix = "  → " if idx == self.current_selection else "    "
                text = f"{prefix}{item_text}"
                if disabled:
                    text += " (unavailable)"
                    
                # Show last used indicator for SSH servers
                if self.in_ssh_menu and idx < len(self.ssh_servers):
                    if self.ssh_servers[idx].get('last_used'):
                        text += " ★"
                        
                # Pad text to clear any previous content
                self.screen.addstr(y, 2, text.ljust(width - 4)[:width - 4], attr)
                
            self.needs_menu_redraw = False
        except:
            pass
            
    def draw_status(self):
        """Draw the connection status section"""
        # Check if status actually changed
        current_state = {
            'backend': self.backend_connected,
            'ssh': self.ssh_connected,
            'remote_ip': self.remote_ip,
            'security': self.security_status,
            'usb_count': len(self.usb_devices)
        }
        
        if (not self.needs_status_redraw and not self.needs_full_redraw and 
            current_state == self.last_drawn_state.get('status', {})):
            return
            
        try:
            height, width = self.screen.getmaxyx()
            status_y = height - 9
            
            # Clear status area
            for y in range(status_y, status_y + 6):
                if y < height:
                    self.screen.move(y, 0)
                    self.screen.clrtoeol()
            
            self.screen.addstr(status_y, 0, "─" * width, curses.color_pair(2))
            self.screen.addstr(status_y + 1, 2, "Connection Status:", curses.A_BOLD)
            
            # Backend status
            backend_color = curses.color_pair(3) if self.backend_connected else curses.color_pair(4)
            backend_text = f"Backend: {'Connected' if self.backend_connected else 'Disconnected'}"
            self.screen.addstr(status_y + 2, 4, backend_text.ljust(40), backend_color)
            
            # SSH status
            ssh_color = curses.color_pair(3) if self.ssh_connected else curses.color_pair(4)
            ssh_text = f"SSH: {'Connected to ' + str(self.remote_ip) if self.ssh_connected else 'Not connected'}"
            self.screen.addstr(status_y + 3, 4, ssh_text.ljust(40), ssh_color)
            
            # Security status
            security_color = curses.color_pair(5) if self.security_status == "Testing" else curses.A_NORMAL
            self.screen.addstr(status_y + 4, 4, f"Security: {self.security_status}".ljust(40), security_color)
            
            # USB devices
            devices_text = f"USB Devices: {len(self.usb_devices)} detected" if self.usb_devices else "USB Devices: None detected"
            self.screen.addstr(status_y + 5, 4, devices_text.ljust(40))
            
            self.last_drawn_state['status'] = current_state.copy()
            self.needs_status_redraw = False
        except:
            pass
            
    def draw_alerts(self):
        """Draw the alerts section at the bottom"""
        if not self.needs_alerts_redraw and not self.needs_full_redraw:
            return
            
        try:
            height, width = self.screen.getmaxyx()
            alerts_y = height - 3
            
            # Clear alerts area
            for y in range(alerts_y - 1, height):
                if y >= 0:
                    self.screen.move(y, 0)
                    self.screen.clrtoeol()
            
            self.screen.addstr(alerts_y - 1, 0, "─" * width, curses.color_pair(2))
            self.screen.addstr(alerts_y, 2, "Alerts:", curses.A_BOLD)
            
            with self.lock:
                recent_alerts = list(self.alerts)[-2:] if len(self.alerts) > 0 else []
                
            for idx, alert in enumerate(recent_alerts):
                if alerts_y + 1 + idx < height:
                    color = curses.A_NORMAL
                    if "ERROR" in alert:
                        color = curses.color_pair(4)
                    elif "WARNING" in alert:
                        color = curses.color_pair(5)
                    elif "SUCCESS" in alert:
                        color = curses.color_pair(3)
                        
                    max_len = width - 4
                    if len(alert) > max_len:
                        alert = alert[:max_len-3] + "..."
                        
                    self.screen.addstr(alerts_y + 1 + idx, 4, alert, color)
                    
            self.needs_alerts_redraw = False
        except:
            pass
            
    def draw_screen(self):
        """Main draw function - only redraws what's needed"""
        if not self.screen:
            return
            
        try:
            if self.needs_full_redraw:
                self.screen.clear()
                self.draw_header()
                self.needs_menu_redraw = True
                self.needs_status_redraw = True
                self.needs_alerts_redraw = True
                self.needs_full_redraw = False
                
            self.draw_menu()
            self.draw_status()
            self.draw_alerts()
            
            # Only refresh if something was drawn
            if self.needs_menu_redraw or self.needs_status_redraw or self.needs_alerts_redraw:
                self.screen.refresh()
        except:
            pass
            
    async def connect_backend(self):
        """Connect to the backend WebSocket server"""
        self.add_alert("Connecting to backend...", "INFO")
        try:
            self.websocket = await websockets.connect("ws://localhost:8765")
            self.backend_connected = True
            self.needs_status_redraw = True
            self.needs_menu_redraw = True  # Menu availability changes
            self.add_alert("Backend connected successfully", "SUCCESS")
            
            # Start listening for messages
            asyncio.create_task(self.listen_for_messages())
        except Exception as e:
            self.add_alert(f"Backend connection failed: {str(e)}", "ERROR")
            
    async def listen_for_messages(self):
        """Listen for messages from backend"""
        try:
            while self.websocket:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
                    data = json.loads(message)
                    await self.handle_backend_message(data)
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    self.add_alert(f"Message error: {str(e)}", "ERROR")
        finally:
            self.backend_connected = False
            self.needs_status_redraw = True
            self.needs_menu_redraw = True
            self.add_alert("Backend disconnected", "WARNING")
            
    async def handle_backend_message(self, data):
        """Handle messages from backend"""
        msg_type = data.get('type')
        
        if msg_type == 'ssh_status':
            old_connected = self.ssh_connected
            self.ssh_connected = data.get('connected', False)
            self.remote_ip = data.get('remote_ip')
            
            if old_connected != self.ssh_connected:
                self.needs_status_redraw = True
                self.needs_menu_redraw = True  # Menu availability changes
                
            if self.ssh_connected:
                self.add_alert(f"SSH connected to {self.remote_ip}", "SUCCESS")
                # Create third pane if needed
                await self.create_ssh_pane()
            else:
                self.add_alert("SSH disconnected", "WARNING")
                
        elif msg_type == 'usb_update':
            old_count = len(self.usb_devices)
            self.usb_devices = data.get('devices', [])
            
            if old_count != len(self.usb_devices):
                self.needs_status_redraw = True
                
            if data.get('new_device'):
                self.add_alert(f"New USB device: {data['new_device']['name']}", "INFO")
                
        elif msg_type == 'security_alert':
            threat = data.get('threat_type', 'Unknown')
            self.add_alert(f"SECURITY THREAT: {threat}", "ERROR")
            self.security_status = "Threat Detected!"
            self.needs_status_redraw = True
            
        elif msg_type == 'test_result':
            test_type = data.get('test_type')
            self.test_results[test_type] = data.get('results', {})
            self.add_alert(f"{test_type} test completed", "SUCCESS")
            
        elif msg_type == 'status_update':
            old_status = self.security_status
            self.security_status = data.get('status', 'Idle')
            if old_status != self.security_status:
                self.needs_status_redraw = True
                
        elif msg_type == 'status':
            # Only add non-empty status messages
            message = data.get('message', '').strip()
            if message:
                self.add_alert(message, "INFO")
                
    async def open_ssh_menu(self):
        """Open SSH server selection menu"""
        self.in_ssh_menu = True
        self.current_selection = 0
        self.init_menu()
        self.needs_menu_redraw = True
        self.add_alert("SSH server menu opened", "INFO")
        
    async def back_to_main(self):
        """Return to main menu"""
        self.in_ssh_menu = False
        self.current_selection = 0
        self.init_menu()
        self.needs_menu_redraw = True
        
    async def connect_to_server(self, server):
        """Connect to selected SSH server"""
        if self.websocket:
            self.add_alert(f"Connecting to {server['name']}...", "INFO")
            
            # Update last used
            self.ssh_manager.update_last_used(server['name'])
            
            # Send connection request
            await self.websocket.send(json.dumps({
                'type': 'connect_ssh',
                'host': server['host'],
                'username': server['username'],
                'password': server.get('password'),
                'key_path': server.get('key_path')
            }))
            
            # Return to main menu
            await self.back_to_main()
            
    async def add_new_server(self):
        """Add new SSH server (placeholder)"""
        self.add_alert("Use launch_enhanced.sh to add servers", "INFO")
        await self.back_to_main()
        
    async def create_ssh_pane(self):
        """Create third pane for SSH session"""
        # This would trigger the pane creation in tmux
        self.add_alert("SSH pane created", "INFO")
        
    async def run_security_test(self):
        """Run security test"""
        if self.websocket and self.backend_connected:
            self.security_status = "Testing"
            self.needs_status_redraw = True
            await self.websocket.send(json.dumps({
                'action': 'run_security_test'
            }))
            self.add_alert("Starting security test...", "INFO")
            
    async def run_performance_test(self):
        """Run performance test"""
        if self.websocket and self.ssh_connected:
            await self.websocket.send(json.dumps({
                'action': 'run_performance_test'
            }))
            self.add_alert("Starting performance test...", "INFO")
            
    async def view_results(self):
        """View test results"""
        if self.test_results:
            self.add_alert(f"Results: {len(self.test_results)} tests completed", "INFO")
        else:
            self.add_alert("No test results available", "INFO")
            
    async def clear_alerts(self):
        """Clear all alerts"""
        with self.lock:
            self.alerts.clear()
            self.needs_alerts_redraw = True
        self.add_alert("Alerts cleared", "INFO")
        
    async def exit_app(self):
        """Exit the application"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            
    async def handle_input(self, key):
        """Handle keyboard input"""
        old_selection = self.current_selection
        
        if key == curses.KEY_UP:
            self.current_selection = (self.current_selection - 1) % len(self.menu_items)
        elif key == curses.KEY_DOWN:
            self.current_selection = (self.current_selection + 1) % len(self.menu_items)
        elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
            _, action = self.menu_items[self.current_selection]
            await action()
        elif key == ord('q'):
            await self.exit_app()
        elif key == 27:  # ESC key
            if self.in_ssh_menu:
                await self.back_to_main()
                
        # Only redraw menu if selection changed
        if old_selection != self.current_selection:
            self.needs_menu_redraw = True
            
    async def run_async(self, screen):
        """Main async run loop"""
        self.screen = screen
        
        # Set up colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        
        # Configure screen
        curses.curs_set(0)
        screen.nodelay(True)
        screen.keypad(True)
        
        self.init_menu()
        
        # Auto-connect to backend
        await self.connect_backend()
        
        # Draw initial screen
        self.needs_full_redraw = True
        self.draw_screen()
        
        while self.running:
            # Only redraw if something changed
            self.draw_screen()
            
            # Handle input
            try:
                key = screen.getch()
                if key != -1:
                    await self.handle_input(key)
            except:
                pass
                
            # Slower refresh rate since we only draw when needed
            await asyncio.sleep(0.1)
            
    def run(self, screen):
        """Bridge between curses and asyncio"""
        try:
            asyncio.run(self.run_async(screen))
        except KeyboardInterrupt:
            pass
            
def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    sys.exit(0)
    
def main():
    """Main entry point"""
    signal.signal(signal.SIGINT, signal_handler)
    
    ui = OptimizedDynamicSSHTerminalUI()
    try:
        curses.wrapper(ui.run)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()