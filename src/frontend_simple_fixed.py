#!/usr/bin/env python3

import asyncio
import websockets
import json
import sys
import threading
from datetime import datetime
import getpass
from typing import Dict
import queue

class SimpleFrontend:
    def __init__(self):
        self.websocket = None
        self.connected = False
        self.running = True
        self.input_queue = queue.Queue()
        
    async def connect_to_backend(self, uri='ws://localhost:8765'):
        """Connect to backend WebSocket server"""
        try:
            self.websocket = await websockets.connect(uri)
            self.connected = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to backend server")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to connect: {e}")
            print("Make sure the backend is running: python src/backend_server.py")
            return False
            
    async def listen_for_messages(self):
        """Listen for messages from backend"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            print("\n[ERROR] Connection to backend lost")
        except Exception as e:
            print(f"\n[ERROR] {e}")
            
    def handle_message(self, data: Dict):
        """Handle message from backend"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        msg_type = data.get('type')
        
        if msg_type == 'status':
            print(f"[{timestamp}] {data.get('message', '')}")
            
        elif msg_type == 'ssh_status':
            if data.get('connected'):
                print(f"[{timestamp}] ✅ SSH connected to {data.get('host')}")
            else:
                print(f"[{timestamp}] ❌ SSH connection failed")
                
        elif msg_type == 'usb_event':
            event = data.get('event')
            device = data.get('device', {})
            print(f"[{timestamp}] USB: {event} - {device.get('name', 'Unknown')} "
                  f"(VID: {device.get('vendor_id')}, PID: {device.get('product_id')})")
            
        elif msg_type == 'security_alert':
            print(f"\n[{timestamp}] ⚠️  SECURITY ALERT ⚠️")
            for threat in data.get('threats', []):
                print(f"  - {threat}")
            print()
                
        elif msg_type == 'security_result':
            if data.get('passed'):
                print(f"\n[{timestamp}] ✅ Cable passed security checks")
                print(f"Cable hash: {data.get('cable_hash', '')[:16]}...\n")
            else:
                print(f"\n[{timestamp}] ❌ Cable FAILED security checks")
                for threat in data.get('threats', []):
                    print(f"  - {threat}")
                print()
                    
        elif msg_type == 'test_progress':
            test = data.get('test')
            print(f"[{timestamp}] Running {test} test...")
            
        elif msg_type == 'test_result':
            test = data.get('test')
            result = data.get('result', {})
            print(f"[{timestamp}] {test} test completed")
            if test == 'data_transfer':
                for r in result.get('results', []):
                    print(f"  - {r['size_mb']}MB: {r['speed_mbps']:.2f} Mbps")
                    
        elif msg_type == 'error':
            print(f"[{timestamp}] ERROR: {data.get('message', 'Unknown error')}")
            
    async def send_command(self, command: Dict):
        """Send command to backend"""
        if self.websocket and self.connected:
            await self.websocket.send(json.dumps(command))
            
    def input_thread(self):
        """Thread to handle blocking input"""
        while self.running:
            try:
                command = input()
                self.input_queue.put(command)
            except EOFError:
                break
            except Exception:
                break
                
    async def process_input(self):
        """Process input from queue"""
        while self.running and self.connected:
            try:
                # Check for input without blocking
                command = self.input_queue.get_nowait()
                
                if command == 'q':
                    self.running = False
                    
                elif command == '1':
                    print("\n--- SSH Connection ---")
                    # For demo, using hardcoded values
                    cmd = {
                        'type': 'connect_ssh',
                        'host': '192.168.1.100',
                        'username': 'testuser',
                        'password': 'testpass'
                    }
                    print("Connecting to 192.168.1.100...")
                    await self.send_command(cmd)
                    
                elif command == '2':
                    print("\nStarting security test...")
                    await self.send_command({'type': 'start_security_test'})
                    
                elif command == '3':
                    print("\nStarting performance tests...")
                    await self.send_command({'type': 'start_performance_test'})
                    
                elif command == '4':
                    await self.send_command({'type': 'get_status'})
                    
                elif command == '5':
                    print("\n🚨 EMERGENCY STOP 🚨")
                    await self.send_command({'type': 'emergency_stop'})
                    
                else:
                    print("Invalid command. Enter 1-5 or q to quit.")
                    
            except queue.Empty:
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Input error: {e}")
                await asyncio.sleep(0.1)
                
    def show_menu(self):
        """Show command menu"""
        print("\n=== Cable Tester Frontend ===")
        print("Commands:")
        print("  1 - Connect SSH to remote Mac")
        print("  2 - Run security test")
        print("  3 - Run performance tests")
        print("  4 - Get status")
        print("  5 - Emergency stop")
        print("  q - Quit")
        print("\nEnter command: ", end='', flush=True)
        
    async def main(self):
        """Main frontend loop"""
        # Connect to backend
        if not await self.connect_to_backend():
            return
            
        # Show menu
        self.show_menu()
        
        # Start input thread
        input_thread = threading.Thread(target=self.input_thread, daemon=True)
        input_thread.start()
        
        try:
            # Start tasks
            listen_task = asyncio.create_task(self.listen_for_messages())
            input_task = asyncio.create_task(self.process_input())
            
            # Wait for tasks
            await asyncio.gather(listen_task, input_task)
            
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.running = False
            if self.websocket:
                await self.websocket.close()

def main():
    frontend = SimpleFrontend()
    asyncio.run(frontend.main())

if __name__ == "__main__":
    main()