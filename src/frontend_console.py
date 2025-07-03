#!/usr/bin/env python3

import asyncio
import websockets
import json
import sys
import threading
from datetime import datetime
import curses
from collections import deque
import getpass

class CableTesterFrontend:
    def __init__(self):
        self.websocket = None
        self.connected = False
        self.message_log = deque(maxlen=100)
        self.test_status = {
            'ssh_connected': False,
            'cable_authorized': False,
            'test_in_progress': False,
            'current_test': None
        }
        self.screen = None
        self.running = True
        
    async def connect_to_backend(self, uri='ws://localhost:8765'):
        """Connect to backend WebSocket server"""
        try:
            self.websocket = await websockets.connect(uri)
            self.connected = True
            self.log_message("Connected to backend server", "SUCCESS")
            return True
        except Exception as e:
            self.log_message(f"Failed to connect: {e}", "ERROR")
            return False
            
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_log.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
    async def listen_for_messages(self):
        """Listen for messages from backend"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_backend_message(data)
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            self.log_message("Connection to backend lost", "ERROR")
            
    async def handle_backend_message(self, data: Dict):
        """Handle message from backend"""
        msg_type = data.get('type')
        
        if msg_type == 'status':
            self.log_message(data.get('message', ''), "INFO")
            
        elif msg_type == 'ssh_status':
            if data.get('connected'):
                self.test_status['ssh_connected'] = True
                self.log_message(f"SSH connected to {data.get('host')}", "SUCCESS")
            else:
                self.log_message("SSH connection failed", "ERROR")
                
        elif msg_type == 'usb_event':
            event = data.get('event')
            device = data.get('device', {})
            self.log_message(
                f"USB Event: {event} - {device.get('name', 'Unknown')} "
                f"(VID: {device.get('vendor_id')}, PID: {device.get('product_id')})",
                "USB"
            )
            
        elif msg_type == 'security_alert':
            self.log_message("⚠️  SECURITY ALERT ⚠️", "ALERT")
            for threat in data.get('threats', []):
                self.log_message(f"  - {threat}", "ALERT")
                
        elif msg_type == 'security_result':
            if data.get('passed'):
                self.test_status['cable_authorized'] = True
                self.log_message("✅ Cable passed security checks", "SUCCESS")
                self.log_message(f"Cable hash: {data.get('cable_hash', '')[:16]}...", "INFO")
            else:
                self.log_message("❌ Cable FAILED security checks", "ERROR")
                for threat in data.get('threats', []):
                    self.log_message(f"  - {threat}", "ERROR")
                    
        elif msg_type == 'test_progress':
            test = data.get('test')
            status = data.get('status')
            self.test_status['current_test'] = test
            self.log_message(f"Running {test} test...", "TEST")
            
        elif msg_type == 'test_result':
            test = data.get('test')
            result = data.get('result', {})
            self.log_message(f"{test} test completed", "TEST")
            # Log specific results based on test type
            
        elif msg_type == 'status_update':
            self.test_status.update(data)
            
        elif msg_type == 'error':
            self.log_message(data.get('message', 'Unknown error'), "ERROR")
            
    async def send_command(self, command: Dict):
        """Send command to backend"""
        if self.websocket and self.connected:
            await self.websocket.send(json.dumps(command))
            
    def init_screen(self):
        """Initialize curses screen"""
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(True)
        curses.start_color()
        
        # Define color pairs
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Success
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)     # Error
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Info
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # USB
        
        # Set non-blocking input
        self.screen.nodelay(True)
        
    def cleanup_screen(self):
        """Cleanup curses screen"""
        if self.screen:
            curses.nocbreak()
            self.screen.keypad(False)
            curses.echo()
            curses.endwin()
            
    def draw_interface(self):
        """Draw the console interface"""
        if not self.screen:
            return
            
        self.screen.clear()
        height, width = self.screen.stdscr.getmaxyx()
        
        # Title
        title = "USB-C/Thunderbolt Cable Tester - Frontend Console"
        self.screen.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
        
        # Status bar
        self.draw_status_bar(2)
        
        # Log window
        self.draw_log_window(5, height - 8)
        
        # Command menu
        self.draw_command_menu(height - 3)
        
        self.screen.refresh()
        
    def draw_status_bar(self, y):
        """Draw status bar"""
        _, width = self.screen.stdscr.getmaxyx()
        
        # Connection status
        backend_status = "Connected" if self.connected else "Disconnected"
        color = curses.color_pair(1) if self.connected else curses.color_pair(2)
        self.screen.addstr(y, 2, f"Backend: {backend_status}", color)
        
        # SSH status
        ssh_status = "Connected" if self.test_status['ssh_connected'] else "Not Connected"
        color = curses.color_pair(1) if self.test_status['ssh_connected'] else curses.color_pair(2)
        self.screen.addstr(y, 25, f"SSH: {ssh_status}", color)
        
        # Cable status
        cable_status = "Authorized" if self.test_status['cable_authorized'] else "Not Authorized"
        color = curses.color_pair(1) if self.test_status['cable_authorized'] else curses.color_pair(2)
        self.screen.addstr(y, 45, f"Cable: {cable_status}", color)
        
        # Test status
        if self.test_status['test_in_progress']:
            test_status = f"Testing: {self.test_status.get('current_test', 'Unknown')}"
            color = curses.color_pair(3)
        else:
            test_status = "Idle"
            color = curses.color_pair(4)
        self.screen.addstr(y, 70, test_status, color)
        
    def draw_log_window(self, start_y, height):
        """Draw log window"""
        _, width = self.screen.stdscr.getmaxyx()
        
        # Border
        self.screen.addstr(start_y - 1, 0, "─" * width)
        self.screen.addstr(start_y - 1, 2, " Log Messages ")
        
        # Log messages
        visible_logs = list(self.message_log)[-height:]
        for i, log in enumerate(visible_logs):
            y = start_y + i
            if y >= start_y + height:
                break
                
            # Color based on level
            color_map = {
                'SUCCESS': curses.color_pair(1),
                'ERROR': curses.color_pair(2),
                'ALERT': curses.color_pair(2) | curses.A_BOLD,
                'WARNING': curses.color_pair(3),
                'INFO': curses.color_pair(4),
                'USB': curses.color_pair(5),
                'TEST': curses.color_pair(4) | curses.A_BOLD
            }
            color = color_map.get(log['level'], curses.color_pair(4))
            
            line = f"{log['timestamp']} [{log['level']:>7}] {log['message']}"
            # Truncate if too long
            if len(line) > width - 2:
                line = line[:width-5] + "..."
                
            self.screen.addstr(y, 1, line, color)
            
    def draw_command_menu(self, y):
        """Draw command menu"""
        _, width = self.screen.stdscr.getmaxyx()
        
        self.screen.addstr(y - 1, 0, "─" * width)
        
        commands = [
            "1: Connect SSH",
            "2: Security Test",
            "3: Performance Test",
            "4: Status",
            "5: Emergency Stop",
            "Q: Quit"
        ]
        
        menu = " | ".join(commands)
        self.screen.addstr(y, (width - len(menu)) // 2, menu)
        
    async def handle_input(self):
        """Handle keyboard input"""
        try:
            key = self.screen.getch()
            
            if key == ord('q') or key == ord('Q'):
                self.running = False
                
            elif key == ord('1'):
                await self.connect_ssh()
                
            elif key == ord('2'):
                await self.send_command({'type': 'start_security_test'})
                
            elif key == ord('3'):
                await self.send_command({'type': 'start_performance_test'})
                
            elif key == ord('4'):
                await self.send_command({'type': 'get_status'})
                
            elif key == ord('5'):
                await self.send_command({'type': 'emergency_stop'})
                
        except curses.error:
            pass
            
    async def connect_ssh(self):
        """Get SSH details and connect"""
        # For demo, using hardcoded values
        # In real app, would prompt for input
        command = {
            'type': 'connect_ssh',
            'host': '192.168.1.100',
            'username': 'testuser',
            'password': 'testpass'
        }
        await self.send_command(command)
        
    async def run_interface(self):
        """Run the interface loop"""
        while self.running and self.connected:
            self.draw_interface()
            await self.handle_input()
            await asyncio.sleep(0.1)
            
    async def main(self):
        """Main frontend loop"""
        # Connect to backend
        if not await self.connect_to_backend():
            print("Failed to connect to backend. Is the backend server running?")
            return
            
        # Initialize screen
        self.init_screen()
        
        try:
            # Start tasks
            listen_task = asyncio.create_task(self.listen_for_messages())
            interface_task = asyncio.create_task(self.run_interface())
            
            # Wait for tasks
            await asyncio.gather(listen_task, interface_task)
            
        except KeyboardInterrupt:
            self.log_message("Shutting down...", "INFO")
        finally:
            self.cleanup_screen()
            if self.websocket:
                await self.websocket.close()

def main():
    frontend = CableTesterFrontend()
    asyncio.run(frontend.main())

if __name__ == "__main__":
    main()