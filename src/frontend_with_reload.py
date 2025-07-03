#!/usr/bin/env python3

import asyncio
import websockets
import json
import sys
import os
import importlib
from datetime import datetime
from typing import Optional
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ReloadableFrontend:
    def __init__(self):
        self.frontend_module = None
        self.frontend_instance = None
        self.websocket = None
        self.running = True
        self.connected = False
        
        # Load the frontend
        self._load_frontend()
        
    def _load_frontend(self):
        """Load or reload the frontend module"""
        try:
            # Import or reload the frontend module
            if self.frontend_module is None:
                self.frontend_module = importlib.import_module('frontend_with_ssh_manager')
            else:
                # Reload related modules
                modules_to_reload = [
                    'frontend_with_ssh_manager',
                    'ssh_manager'
                ]
                
                for module_name in modules_to_reload:
                    if module_name in sys.modules:
                        importlib.reload(sys.modules[module_name])
                
                self.frontend_module = importlib.reload(self.frontend_module)
            
            # Create new frontend instance
            FrontendClass = getattr(self.frontend_module, 'CableTesterFrontend')
            self.frontend_instance = FrontendClass()
            
            # Restore WebSocket connection if exists
            if self.websocket and self.connected:
                self.frontend_instance.websocket = self.websocket
                self.frontend_instance.connected = True
            
            print("\n✅ Frontend reloaded successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Failed to reload frontend: {e}")
            traceback.print_exc()
            return False
    
    async def connect_to_backend(self):
        """Connect to the backend WebSocket server"""
        uri = "ws://localhost:8765"
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries and self.running:
            try:
                print(f"Connecting to backend at {uri}...")
                self.websocket = await websockets.connect(uri)
                self.connected = True
                
                # Update frontend instance
                if self.frontend_instance:
                    self.frontend_instance.websocket = self.websocket
                    self.frontend_instance.connected = True
                
                print("✅ Connected to backend successfully!")
                return True
                
            except Exception as e:
                retry_count += 1
                print(f"Connection failed (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    await asyncio.sleep(2)
        
        return False
    
    async def handle_messages(self):
        """Handle incoming messages from backend"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    # Check for reload status messages
                    if data.get('type') == 'reload_status':
                        status = data.get('status')
                        msg = data.get('message', '')
                        
                        if status == 'starting':
                            print(f"\n🔄 Backend reload: {msg}")
                        elif status == 'complete':
                            print(f"✅ Backend reload: {msg}")
                        elif status == 'failed':
                            print(f"❌ Backend reload: {msg}")
                    else:
                        # Forward to frontend instance
                        if self.frontend_instance:
                            await self.frontend_instance.handle_message(data)
                        
                except json.JSONDecodeError:
                    print("Received invalid JSON from backend")
                except Exception as e:
                    print(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("\n❌ Lost connection to backend")
            self.connected = False
            if self.frontend_instance:
                self.frontend_instance.connected = False
    
    async def run_frontend_loop(self):
        """Run the frontend main loop"""
        while self.running:
            try:
                # Let frontend process one iteration
                if self.frontend_instance and hasattr(self.frontend_instance, 'run_once'):
                    should_continue = await self.frontend_instance.run_once()
                    if not should_continue:
                        self.running = False
                        break
                else:
                    # Fallback: simple command loop
                    await self.simple_command_loop()
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                self.running = False
            except Exception as e:
                print(f"\nError in frontend loop: {e}")
                traceback.print_exc()
                await asyncio.sleep(1)
    
    async def simple_command_loop(self):
        """Simple command loop when frontend doesn't have run_once"""
        print("\n=== Reloadable Frontend (Fallback Mode) ===")
        print("Commands:")
        print("  reload  - Reload frontend code")
        print("  reload-backend - Reload backend code")
        print("  status  - Check connection status")
        print("  exit    - Exit the application")
        print("")
        
        command = input("> ").strip().lower()
        
        if command == "exit":
            self.running = False
        elif command == "reload":
            self._load_frontend()
        elif command == "reload-backend":
            if self.websocket and self.connected:
                await self.websocket.send(json.dumps({'type': 'reload_backend'}))
                print("Sent reload command to backend")
            else:
                print("Not connected to backend")
        elif command == "status":
            print(f"Connected: {self.connected}")
            print(f"Frontend loaded: {self.frontend_instance is not None}")
        else:
            print("Unknown command")
    
    async def run(self):
        """Main run method"""
        print("\n🚀 Starting Reloadable Cable Tester Frontend")
        print("This frontend supports hot reloading!")
        print("")
        
        # Connect to backend
        if not await self.connect_to_backend():
            print("Failed to connect to backend. Exiting.")
            return
        
        # Create tasks
        message_task = asyncio.create_task(self.handle_messages())
        frontend_task = asyncio.create_task(self.run_frontend_loop())
        
        # Wait for either task to complete
        done, pending = await asyncio.gather(
            message_task,
            frontend_task,
            return_exceptions=True
        )
        
        # Clean up
        if self.websocket:
            await self.websocket.close()
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
        
        print("\n✅ Frontend shutdown complete")

def main():
    """Main entry point"""
    frontend = ReloadableFrontend()
    
    try:
        asyncio.run(frontend.run())
    except KeyboardInterrupt:
        print("\n\nShutdown complete")
    except Exception as e:
        print(f"\nFatal error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()