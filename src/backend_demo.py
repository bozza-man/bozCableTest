#!/usr/bin/env python3

import asyncio
import websockets
import json
from datetime import datetime

class DemoBackend:
    def __init__(self):
        self.clients = set()
        
    async def handle_client(self, websocket):
        """Handle client connection"""
        # Register client
        self.clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'connection',
            'status': 'connected',
            'backend_version': '1.0 (Demo)'
        }))
        
        try:
            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                await self.process_command(websocket, data)
                
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        finally:
            self.clients.remove(websocket)
            
    async def process_command(self, websocket, command):
        """Process commands from frontend"""
        cmd_type = command.get('type')
        print(f"Received command: {cmd_type}")
        
        if cmd_type == 'connect_ssh':
            # Simulate SSH connection
            await self.broadcast({
                'type': 'status',
                'message': 'Connecting to remote Mac...'
            })
            
            await asyncio.sleep(2)  # Simulate connection time
            
            await self.broadcast({
                'type': 'ssh_status',
                'connected': True,
                'host': command.get('host', 'demo-host')
            })
            
        elif cmd_type == 'start_security_test':
            # Simulate security test
            await self.broadcast({
                'type': 'status',
                'message': 'Starting security test...'
            })
            
            await asyncio.sleep(1)
            
            await self.broadcast({
                'type': 'status',
                'message': 'Please connect the cable now...',
                'waiting_for_cable': True
            })
            
            await asyncio.sleep(3)
            
            # Simulate cable detection
            await self.broadcast({
                'type': 'usb_event',
                'event': 'device_added',
                'device': {
                    'name': 'USB-C Cable (Demo)',
                    'vendor_id': '0x05ac',
                    'product_id': '0x1234'
                }
            })
            
            await asyncio.sleep(2)
            
            # Simulate security result
            await self.broadcast({
                'type': 'security_result',
                'passed': True,
                'threats': [],
                'cable_hash': 'demo1234567890abcdef'
            })
            
        elif cmd_type == 'start_performance_test':
            # Simulate performance tests
            tests = ['data_transfer', 'power_delivery', 'thunderbolt', 'signal_integrity']
            
            for test in tests:
                await self.broadcast({
                    'type': 'test_progress',
                    'test': test,
                    'status': 'running'
                })
                
                await asyncio.sleep(2)
                
                result = {}
                if test == 'data_transfer':
                    result = {
                        'results': [
                            {'size_mb': 1, 'speed_mbps': 480},
                            {'size_mb': 10, 'speed_mbps': 4800},
                            {'size_mb': 100, 'speed_mbps': 5000}
                        ]
                    }
                    
                await self.broadcast({
                    'type': 'test_result',
                    'test': test,
                    'result': result
                })
                
        elif cmd_type == 'get_status':
            await self.broadcast({
                'type': 'status_update',
                'test_in_progress': False,
                'cable_authorized': True,
                'ssh_connected': True,
                'protection_status': {
                    'lockdown_mode': False,
                    'blocked_devices': [],
                    'monitoring': True
                }
            })
            
        elif cmd_type == 'emergency_stop':
            await self.broadcast({
                'type': 'status',
                'message': 'Emergency stop activated!'
            })
            
            await self.broadcast({
                'type': 'emergency_stop_complete'
            })
            
    async def broadcast(self, message):
        """Broadcast message to all clients"""
        if self.clients:
            message_str = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_str) for client in self.clients],
                return_exceptions=True
            )
            
    async def start_server(self):
        """Start WebSocket server"""
        print("Demo Backend starting on ws://localhost:8765")
        print("This is a demonstration backend - no actual cable testing occurs")
        print()
        
        async with websockets.serve(self.handle_client, "localhost", 8765):
            await asyncio.Future()  # Run forever

def main():
    backend = DemoBackend()
    asyncio.run(backend.start_server())

if __name__ == "__main__":
    main()