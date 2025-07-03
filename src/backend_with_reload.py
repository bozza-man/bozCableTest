#!/usr/bin/env python3

import asyncio
import websockets
import json
import importlib
import sys
import os
import signal
from typing import Dict, Set, Optional
from datetime import datetime
import traceback

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ReloadableBackend:
    def __init__(self, debug=False):
        self.debug = debug
        self.backend_module = None
        self.backend_instance = None
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.running = True
        self.reload_lock = asyncio.Lock()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Load the backend
        self._load_backend()
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False
        
    def _load_backend(self):
        """Load or reload the backend module"""
        try:
            # Import or reload the backend module
            if self.backend_module is None:
                self.backend_module = importlib.import_module('backend_server_logged')
            else:
                # Stop existing backend cleanly
                if self.backend_instance:
                    print("Stopping existing backend instance...")
                    if hasattr(self.backend_instance, 'usb_monitor'):
                        self.backend_instance.usb_monitor.stop_monitoring()
                    if hasattr(self.backend_instance, 'security_monitor'):
                        if hasattr(self.backend_instance.security_monitor, 'bruteforce_protection'):
                            self.backend_instance.security_monitor.bruteforce_protection.stop_monitoring()
                
                # Reload all related modules
                modules_to_reload = [
                    'backend_server_logged',
                    'usb_monitor',
                    'security_monitor',
                    'ssh_manager',
                    'bruteforce_protection',
                    'packet_inspector',
                    'logger_config'
                ]
                
                for module_name in modules_to_reload:
                    if module_name in sys.modules:
                        importlib.reload(sys.modules[module_name])
                
                self.backend_module = importlib.reload(self.backend_module)
            
            # Create new backend instance
            BackendClass = getattr(self.backend_module, 'CableTesterBackend')
            self.backend_instance = BackendClass(debug=self.debug)
            
            # Restore client connections
            self.backend_instance.connected_clients = self.connected_clients
            
            print("✅ Backend loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load backend: {e}")
            traceback.print_exc()
            return False
    
    async def handle_client(self, websocket, path):
        """Handle client WebSocket connection"""
        # Register client
        self.connected_clients.add(websocket)
        print(f"Client connected from {websocket.remote_address}. Total: {len(self.connected_clients)}")
        
        # Send connection confirmation
        await websocket.send(json.dumps({
            'type': 'connection',
            'status': 'connected',
            'backend_version': '2.0-reloadable',
            'features': ['hot-reload', 'in-place-update']
        }))
        
        try:
            async for message in websocket:
                if not self.running:
                    break
                
                try:
                    command = json.loads(message)
                    
                    # Check for reload command
                    if command.get('type') == 'reload_backend':
                        await self.handle_reload(websocket)
                    else:
                        # Forward to backend instance
                        if self.backend_instance:
                            await self.backend_instance.process_command(command)
                        else:
                            await websocket.send(json.dumps({
                                'type': 'error',
                                'message': 'Backend not loaded'
                            }))
                            
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    }))
                except Exception as e:
                    print(f"Error processing command: {e}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': str(e)
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"Client disconnected")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            # Unregister client
            self.connected_clients.discard(websocket)
            if self.backend_instance:
                self.backend_instance.connected_clients.discard(websocket)
            print(f"Client removed. Total: {len(self.connected_clients)}")
    
    async def handle_reload(self, websocket):
        """Handle reload request"""
        async with self.reload_lock:
            print("\n🔄 Reloading backend...")
            
            # Notify all clients
            await self.broadcast_message({
                'type': 'reload_status',
                'status': 'starting',
                'message': 'Backend reload initiated...'
            })
            
            # Perform reload
            success = self._load_backend()
            
            if success:
                # Re-setup the message broadcaster
                if hasattr(self.backend_instance, 'message_queue'):
                    # Transfer any pending messages
                    pass
                
                await self.broadcast_message({
                    'type': 'reload_status',
                    'status': 'complete',
                    'message': 'Backend reloaded successfully!'
                })
            else:
                await self.broadcast_message({
                    'type': 'reload_status',
                    'status': 'failed',
                    'message': 'Backend reload failed. Check server logs.'
                })
    
    async def broadcast_message(self, message: Dict):
        """Broadcast message to all connected clients"""
        if self.connected_clients:
            message_str = json.dumps(message)
            # Send to all clients
            disconnected = []
            for client in self.connected_clients:
                try:
                    await client.send(message_str)
                except:
                    disconnected.append(client)
            
            # Remove disconnected clients
            for client in disconnected:
                self.connected_clients.discard(client)
    
    async def message_forwarder(self):
        """Forward messages from backend instance to clients"""
        while self.running:
            try:
                if self.backend_instance and hasattr(self.backend_instance, 'message_queue'):
                    # Get messages from backend queue
                    messages = []
                    while not self.backend_instance.message_queue.empty():
                        try:
                            messages.append(self.backend_instance.message_queue.get_nowait())
                        except:
                            break
                    
                    # Broadcast all messages
                    for message in messages:
                        await self.broadcast_message(message)
                
            except Exception as e:
                print(f"Message forwarder error: {e}")
            
            await asyncio.sleep(0.1)
    
    async def start_server(self, host='localhost', port=8765):
        """Start the reloadable WebSocket server"""
        print(f"\n🚀 Starting Reloadable Cable Tester Backend on ws://{host}:{port}")
        print("Commands:")
        print("  - Send {'type': 'reload_backend'} to reload the backend code")
        print("  - All other commands are forwarded to the backend instance")
        print("")
        
        # Start message forwarder
        asyncio.create_task(self.message_forwarder())
        
        # Start WebSocket server
        async with websockets.serve(self.handle_client, host, port) as server:
            self.server = server
            print(f"✅ Server started successfully")
            
            # Keep server running
            while self.running:
                await asyncio.sleep(1)
            
            print("\nShutting down server...")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Reloadable Cable Tester Backend')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--port', type=int, default=8765, help='WebSocket port')
    args = parser.parse_args()
    
    try:
        server = ReloadableBackend(debug=args.debug)
        asyncio.run(server.start_server(port=args.port))
    except KeyboardInterrupt:
        print("\n✅ Shutdown complete")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()