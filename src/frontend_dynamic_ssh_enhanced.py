#!/usr/bin/env python3
"""
Enhanced Dynamic Terminal Frontend with Full SSH Server Management
Includes add, edit, delete functionality with form inputs
"""

import asyncio
import websockets
import json
import sys
import os
import curses
import curses.textpad
from datetime import datetime
from collections import deque
import threading
import signal
from typing import Optional, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ssh_server_manager import SSHServerManager

class EnhancedDynamicUI:
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
        
        # Menu states
        self.menu_state = "main"  # main, ssh_list, ssh_edit, ssh_add, ssh_delete
        self.ssh_servers = []
        self.selected_server = None
        self.form_data = {}
        self.form_field = 0
        self.input_buffer = ""
        self.input_active = False
        
        # Track what needs redrawing
        self.needs_full_redraw = True
        self.needs_menu_redraw = False
        self.needs_status_redraw = False
        self.needs_alerts_redraw = False
        self.last_drawn_state = {}
        
    def init_menu(self):
        """Initialize menu items based on current state"""
        old_menu_count = len(self.menu_items)
        
        if self.menu_state == "main":
            self.menu_items = [
                ("Connect to Backend", self.connect_backend),
                ("SSH Server Management", self.open_ssh_menu),
                ("Run Security Test", self.run_security_test),
                ("Run Performance Test", self.run_performance_test),
                ("View Test Results", self.view_results),
                ("Clear Alerts", self.clear_alerts),
                ("Exit", self.exit_app)
            ]
            
        elif self.menu_state == "ssh_list":
            self.menu_items = []
            self.ssh_servers = self.ssh_manager.list_servers()
            
            # Add existing servers
            for server in self.ssh_servers:
                star = " ★" if server.get('last_used') else ""
                self.menu_items.append((
                    f"{server['name']} ({server['host']}){star}",
                    lambda s=server: self.select_server_action(s)
                ))
            
            # Add management options
            self.menu_items.extend([
                ("─" * 30, None),  # Separator
                ("Add New Server", self.add_new_server),
                ("Back to Main Menu", self.back_to_main)
            ])
            
        elif self.menu_state == "ssh_edit":
            if self.selected_server:
                self.menu_items = [
                    (f"Editing: {self.selected_server['name']}", None),
                    ("─" * 30, None),
                    ("Connect to this server", self.connect_to_selected),
                    ("Edit server details", self.edit_server_details),
                    ("Delete this server", self.confirm_delete_server),
                    ("Back to server list", self.back_to_ssh_list)
                ]
                
        elif self.menu_state == "ssh_add":
            # Form mode - no menu items
            self.menu_items = []
            
        elif self.menu_state == "ssh_delete":
            if self.selected_server:
                self.menu_items = [
                    (f"Delete server: {self.selected_server['name']}?", None),
                    ("─" * 30, None),
                    ("Yes, delete this server", self.delete_server),
                    ("No, keep this server", self.back_to_ssh_edit)
                ]
        
        if old_menu_count != len(self.menu_items) or self.menu_state != self.last_drawn_state.get('menu_state'):
            self.needs_menu_redraw = True
            self.needs_full_redraw = True
            
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
            
            self.screen.move(0, 0)
            self.screen.clrtoeol()
            self.screen.move(1, 0)
            self.screen.clrtoeol()
            
            self.screen.addstr(0, (width - len(header)) // 2, header, 
                             curses.A_BOLD | curses.color_pair(1))
            self.screen.addstr(1, 0, "─" * width, curses.color_pair(2))
        except:
            pass
            
    def draw_menu(self):
        """Draw the interactive menu or form"""
        if not self.needs_menu_redraw and not self.needs_full_redraw:
            return
            
        try:
            height, width = self.screen.getmaxyx()
            menu_start_y = 3
            
            # Clear menu area
            for y in range(menu_start_y, height - 10):
                self.screen.move(y, 0)
                self.screen.clrtoeol()
            
            if self.menu_state == "ssh_add" or (self.menu_state == "ssh_edit" and self.input_active):
                self.draw_server_form(menu_start_y)
            else:
                # Draw regular menu
                title = {
                    "main": "Main Menu:",
                    "ssh_list": "SSH Servers:",
                    "ssh_edit": "Server Actions:",
                    "ssh_delete": "Confirm Delete:"
                }.get(self.menu_state, "Menu:")
                
                self.screen.addstr(menu_start_y, 2, title, curses.A_BOLD)
                
                for idx, item in enumerate(self.menu_items):
                    y = menu_start_y + 2 + idx
                    if y >= height - 10:
                        break
                    
                    item_text, action = item
                    
                    # Skip separators for selection
                    if action is None and "─" in item_text:
                        self.screen.addstr(y, 2, item_text[:width-4], curses.color_pair(2))
                        continue
                    
                    # Disable certain options
                    disabled = False
                    if self.menu_state == "main":
                        if not self.backend_connected and item_text not in ["Connect to Backend", "Exit"]:
                            disabled = True
                        elif not self.ssh_connected and item_text in ["Run Security Test", "Run Performance Test"]:
                            disabled = True
                    
                    # Calculate actual selectable index
                    selectable_idx = self.get_selectable_index(idx)
                    
                    if selectable_idx == self.current_selection and action is not None:
                        attr = curses.A_REVERSE
                    else:
                        attr = curses.A_DIM if disabled else curses.A_NORMAL
                    
                    prefix = "  → " if selectable_idx == self.current_selection and action is not None else "    "
                    text = f"{prefix}{item_text}"
                    if disabled:
                        text += " (unavailable)"
                    
                    self.screen.addstr(y, 2, text.ljust(width - 4)[:width - 4], attr)
                
            self.needs_menu_redraw = False
            self.last_drawn_state['menu_state'] = self.menu_state
        except:
            pass
            
    def draw_server_form(self, start_y):
        """Draw the server add/edit form"""
        try:
            height, width = self.screen.getmaxyx()
            
            title = "Add New Server" if self.menu_state == "ssh_add" else "Edit Server"
            self.screen.addstr(start_y, 2, title, curses.A_BOLD)
            self.screen.addstr(start_y + 1, 2, "─" * 40, curses.color_pair(2))
            
            fields = [
                ("Server Name", "name", "my-server"),
                ("Host/IP", "host", "192.168.1.100"),
                ("Username", "username", "user"),
                ("Port", "port", "22"),
                ("SSH Key Path", "key_path", "/path/to/key (optional)")
            ]
            
            for idx, (label, field, placeholder) in enumerate(fields):
                y = start_y + 3 + (idx * 2)
                if y >= height - 12:
                    break
                
                # Draw label
                self.screen.addstr(y, 4, f"{label}:", curses.A_BOLD)
                
                # Get current value
                if self.menu_state == "ssh_edit" and self.selected_server and not self.input_active:
                    value = str(self.selected_server.get(field, ''))
                else:
                    value = self.form_data.get(field, '')
                
                # Draw input field
                if idx == self.form_field and self.input_active:
                    # Active field - show cursor
                    display_value = self.input_buffer
                    attr = curses.A_REVERSE
                else:
                    display_value = value or placeholder
                    attr = curses.A_NORMAL if value else curses.A_DIM
                
                # Draw field background
                field_width = min(40, width - 20)
                self.screen.addstr(y + 1, 6, "[" + " " * field_width + "]", curses.color_pair(2))
                
                # Draw field value
                if len(display_value) > field_width - 2:
                    display_value = display_value[-(field_width-2):]
                self.screen.addstr(y + 1, 7, display_value.ljust(field_width - 1)[:field_width - 1], attr)
                
                # Show field selection
                if idx == self.form_field:
                    self.screen.addstr(y + 1, 4, "→", curses.A_BOLD)
            
            # Draw form actions
            y = start_y + 3 + (len(fields) * 2) + 1
            if y < height - 10:
                self.screen.addstr(y, 2, "─" * 40, curses.color_pair(2))
                y += 1
                
                if self.input_active:
                    self.screen.addstr(y, 4, "Enter: Save field | ESC: Cancel input", curses.color_pair(5))
                else:
                    self.screen.addstr(y, 4, "↑/↓: Select field | Enter: Edit field", curses.A_DIM)
                    y += 1
                    self.screen.addstr(y, 4, "S: Save server | ESC: Cancel", curses.A_DIM)
                    
        except Exception as e:
            self.add_alert(f"Form error: {str(e)}", "ERROR")
            
    def get_selectable_index(self, visual_idx):
        """Convert visual index to selectable index (skip separators)"""
        selectable = 0
        for i in range(visual_idx + 1):
            if i < len(self.menu_items) and self.menu_items[i][1] is not None:
                selectable += 1
        return selectable - 1
        
    def get_visual_index(self, selectable_idx):
        """Convert selectable index to visual index"""
        count = 0
        for i, (_, action) in enumerate(self.menu_items):
            if action is not None:
                if count == selectable_idx:
                    return i
                count += 1
        return 0
        
    def draw_status(self):
        """Draw the connection status section"""
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
            
            for y in range(status_y, status_y + 6):
                if y < height:
                    self.screen.move(y, 0)
                    self.screen.clrtoeol()
            
            self.screen.addstr(status_y, 0, "─" * width, curses.color_pair(2))
            self.screen.addstr(status_y + 1, 2, "Connection Status:", curses.A_BOLD)
            
            # Status lines
            backend_color = curses.color_pair(3) if self.backend_connected else curses.color_pair(4)
            self.screen.addstr(status_y + 2, 4, f"Backend: {'Connected' if self.backend_connected else 'Disconnected'}".ljust(40), backend_color)
            
            ssh_color = curses.color_pair(3) if self.ssh_connected else curses.color_pair(4)
            ssh_text = f"SSH: {'Connected to ' + str(self.remote_ip) if self.ssh_connected else 'Not connected'}"
            self.screen.addstr(status_y + 3, 4, ssh_text.ljust(40), ssh_color)
            
            security_color = curses.color_pair(5) if self.security_status == "Testing" else curses.A_NORMAL
            self.screen.addstr(status_y + 4, 4, f"Security: {self.security_status}".ljust(40), security_color)
            
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
        """Main draw function"""
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
            self.needs_menu_redraw = True
            self.add_alert("Backend connected successfully", "SUCCESS")
            
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
                    break
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
                self.needs_menu_redraw = True
                
            if self.ssh_connected:
                self.add_alert(f"SSH connected to {self.remote_ip}", "SUCCESS")
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
            message = data.get('message', '').strip()
            if message:
                self.add_alert(message, "INFO")
                
    # Menu action methods
    async def open_ssh_menu(self):
        """Open SSH server list"""
        self.menu_state = "ssh_list"
        self.current_selection = 0
        self.init_menu()
        self.add_alert("SSH server management opened", "INFO")
        
    async def back_to_main(self):
        """Return to main menu"""
        self.menu_state = "main"
        self.current_selection = 0
        self.init_menu()
        
    async def back_to_ssh_list(self):
        """Return to SSH server list"""
        self.menu_state = "ssh_list"
        self.current_selection = 0
        self.selected_server = None
        self.init_menu()
        
    async def back_to_ssh_edit(self):
        """Return to SSH edit menu"""
        self.menu_state = "ssh_edit"
        self.current_selection = 0
        self.init_menu()
        
    async def select_server_action(self, server):
        """Handle server selection"""
        self.selected_server = server
        self.menu_state = "ssh_edit"
        self.current_selection = 0
        self.init_menu()
        
    async def connect_to_selected(self):
        """Connect to the selected server"""
        if self.selected_server and self.websocket:
            self.add_alert(f"Connecting to {self.selected_server['name']}...", "INFO")
            
            # Update last used
            self.ssh_manager.select_server(self.selected_server['name'])
            
            # Send connection request
            await self.websocket.send(json.dumps({
                'type': 'connect_ssh',
                'host': self.selected_server['host'],
                'username': self.selected_server['username'],
                'password': self.selected_server.get('password'),
                'key_path': self.selected_server.get('key_path'),
                'port': self.selected_server.get('port', 22)
            }))
            
            # Return to main menu
            await self.back_to_main()
            
    async def add_new_server(self):
        """Start adding a new server"""
        self.menu_state = "ssh_add"
        self.form_data = {}
        self.form_field = 0
        self.input_active = False
        self.init_menu()
        self.add_alert("Adding new server - use ↑/↓ to select fields", "INFO")
        
    async def edit_server_details(self):
        """Edit existing server"""
        if self.selected_server:
            self.menu_state = "ssh_edit"
            self.form_data = self.selected_server.copy()
            self.form_field = 0
            self.input_active = True
            self.input_buffer = ""
            self.needs_full_redraw = True
            self.add_alert("Editing server - use ↑/↓ to select fields", "INFO")
            
    async def confirm_delete_server(self):
        """Confirm server deletion"""
        self.menu_state = "ssh_delete"
        self.current_selection = 0
        self.init_menu()
        
    async def delete_server(self):
        """Actually delete the server"""
        if self.selected_server:
            name = self.selected_server['name']
            if self.ssh_manager.remove_server(name):
                self.add_alert(f"Server '{name}' deleted", "SUCCESS")
            else:
                self.add_alert(f"Failed to delete server '{name}'", "ERROR")
            
            await self.back_to_ssh_list()
            
    async def save_server_form(self):
        """Save the server form data"""
        required_fields = ['name', 'host', 'username']
        
        # Validate required fields
        for field in required_fields:
            if not self.form_data.get(field):
                self.add_alert(f"Field '{field}' is required", "ERROR")
                return
                
        # Convert port to int
        try:
            port = int(self.form_data.get('port', 22))
        except ValueError:
            port = 22
            
        # Clean up optional fields
        key_path = self.form_data.get('key_path', '')
        if key_path and 'optional' in key_path.lower():
            key_path = None
            
        if self.menu_state == "ssh_add":
            # Add new server
            success = self.ssh_manager.add_server(
                name=self.form_data['name'],
                host=self.form_data['host'],
                username=self.form_data['username'],
                port=port,
                key_path=key_path
            )
            
            if success:
                self.add_alert(f"Server '{self.form_data['name']}' added", "SUCCESS")
                await self.back_to_ssh_list()
            else:
                self.add_alert("Server name already exists", "ERROR")
        else:
            # Update existing server
            old_name = self.selected_server['name']
            
            # If name changed, we need to remove and re-add
            if old_name != self.form_data['name']:
                self.ssh_manager.remove_server(old_name)
                
            success = self.ssh_manager.add_server(
                name=self.form_data['name'],
                host=self.form_data['host'],
                username=self.form_data['username'],
                port=port,
                key_path=key_path
            )
            
            if success:
                self.add_alert(f"Server '{self.form_data['name']}' updated", "SUCCESS")
                await self.back_to_ssh_list()
            else:
                self.add_alert("Failed to update server", "ERROR")
                
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
        if self.input_active:
            # Handle text input mode
            if key == 27:  # ESC
                self.input_active = False
                self.input_buffer = ""
                self.needs_menu_redraw = True
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                # Save the current field
                fields = ["name", "host", "username", "port", "key_path"]
                if self.form_field < len(fields):
                    self.form_data[fields[self.form_field]] = self.input_buffer
                self.input_active = False
                self.input_buffer = ""
                self.needs_menu_redraw = True
            elif key == curses.KEY_BACKSPACE or key == 127:
                if self.input_buffer:
                    self.input_buffer = self.input_buffer[:-1]
                    self.needs_menu_redraw = True
            elif 32 <= key <= 126:  # Printable characters
                self.input_buffer += chr(key)
                self.needs_menu_redraw = True
                
        elif self.menu_state in ["ssh_add", "ssh_edit"] and self.menu_state == "ssh_edit" and self.input_active == False:
            # Form navigation mode
            if key == curses.KEY_UP:
                self.form_field = max(0, self.form_field - 1)
                self.needs_menu_redraw = True
            elif key == curses.KEY_DOWN:
                self.form_field = min(4, self.form_field + 1)  # 5 fields total
                self.needs_menu_redraw = True
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                # Start editing the field
                fields = ["name", "host", "username", "port", "key_path"]
                current_value = self.form_data.get(fields[self.form_field], '')
                if self.menu_state == "ssh_edit" and self.selected_server:
                    current_value = str(self.selected_server.get(fields[self.form_field], ''))
                self.input_buffer = current_value
                self.input_active = True
                self.needs_menu_redraw = True
            elif key == ord('s') or key == ord('S'):
                await self.save_server_form()
            elif key == 27:  # ESC
                if self.menu_state == "ssh_add":
                    await self.back_to_ssh_list()
                else:
                    self.input_active = False
                    await self.back_to_ssh_edit()
                    
        else:
            # Regular menu navigation
            old_selection = self.current_selection
            
            if key == curses.KEY_UP:
                # Count selectable items
                selectable_count = sum(1 for _, action in self.menu_items if action is not None)
                self.current_selection = (self.current_selection - 1) % selectable_count
            elif key == curses.KEY_DOWN:
                selectable_count = sum(1 for _, action in self.menu_items if action is not None)
                self.current_selection = (self.current_selection + 1) % selectable_count
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                # Find the actual menu item for this selection
                visual_idx = self.get_visual_index(self.current_selection)
                if visual_idx < len(self.menu_items):
                    _, action = self.menu_items[visual_idx]
                    if action:
                        await action()
            elif key == ord('q'):
                await self.exit_app()
            elif key == 27:  # ESC
                if self.menu_state != "main":
                    await self.back_to_main()
                    
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
        
        self.needs_full_redraw = True
        self.draw_screen()
        
        while self.running:
            self.draw_screen()
            
            try:
                key = screen.getch()
                if key != -1:
                    await self.handle_input(key)
            except:
                pass
                
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
    
    ui = EnhancedDynamicUI()
    try:
        curses.wrapper(ui.run)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()