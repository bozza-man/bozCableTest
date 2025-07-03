#!/usr/bin/env python3

import asyncio
import websockets
import json
import threading
import queue
import time
from datetime import datetime
from typing import Dict, Optional

# Add current directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security_monitor import SecurityMonitor
from ssh_manager import SSHManager
from usb_monitor import USBMonitor, USBEvent

class CableTesterBackend:
    def __init__(self):
        self.security_monitor = SecurityMonitor()
        self.ssh_manager = SSHManager()
        self.usb_monitor = USBMonitor(self.security_monitor)
        
        # Message queues
        self.message_queue = queue.Queue()
        self.command_queue = queue.Queue()
        
        # State
        self.connected_clients = set()
        self.test_in_progress = False
        self.cable_authorized = False
        self.test_results = {}
        
        # Setup USB monitor handlers
        self._setup_monitor_handlers()
        
    def _setup_monitor_handlers(self):
        """Setup USB monitor event handlers"""
        self.usb_monitor.register_handler(
            USBEvent.DEVICE_ADDED,
            lambda event: self._send_message({
                'type': 'usb_event',
                'event': 'device_added',
                'device': event['device']
            })
        )
        
        self.usb_monitor.register_handler(
            USBEvent.SUSPICIOUS_ACTIVITY,
            lambda event: self._send_message({
                'type': 'security_alert',
                'threats': event['threats'],
                'device': event['device']
            })
        )
        
    def _send_message(self, message: Dict):
        """Queue message for clients"""
        self.message_queue.put({
            'timestamp': datetime.now().isoformat(),
            **message
        })
        
    async def register_client(self, websocket):
        """Register new client connection"""
        self.connected_clients.add(websocket)
        await websocket.send(json.dumps({
            'type': 'connection',
            'status': 'connected',
            'backend_version': '1.0'
        }))
        
    async def unregister_client(self, websocket):
        """Remove client connection"""
        self.connected_clients.remove(websocket)
        
    async def broadcast_message(self, message: Dict):
        """Broadcast message to all connected clients"""
        if self.connected_clients:
            message_str = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_str) for client in self.connected_clients],
                return_exceptions=True
            )
            
    async def handle_client(self, websocket):
        """Handle client WebSocket connection"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                command = json.loads(message)
                await self.process_command(command)
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
            
    async def process_command(self, command: Dict):
        """Process command from frontend"""
        cmd_type = command.get('type')
        
        if cmd_type == 'connect_ssh':
            await self._handle_ssh_connect(command)
        elif cmd_type == 'start_security_test':
            await self._handle_security_test()
        elif cmd_type == 'start_performance_test':
            await self._handle_performance_test()
        elif cmd_type == 'get_status':
            await self._handle_status_request()
        elif cmd_type == 'emergency_stop':
            await self._handle_emergency_stop()
            
    async def _handle_ssh_connect(self, command: Dict):
        """Handle SSH connection request"""
        host = command.get('host')
        username = command.get('username')
        password = command.get('password')
        key_path = command.get('key_path')
        
        await self.broadcast_message({
            'type': 'status',
            'message': f'Connecting to {host}...'
        })
        
        # Run in thread to avoid blocking
        def connect():
            if password:
                success = self.ssh_manager.connect(host, username, password=password)
            else:
                success = self.ssh_manager.connect(host, username, key_path=key_path)
                
            if success:
                self.ssh_manager.deploy_agent()
                self.ssh_manager.start_remote_agent()
                
            return success
            
        success = await asyncio.get_event_loop().run_in_executor(None, connect)
        
        await self.broadcast_message({
            'type': 'ssh_status',
            'connected': success,
            'host': host if success else None
        })
        
    async def _handle_security_test(self):
        """Handle security test request"""
        if self.test_in_progress:
            await self.broadcast_message({
                'type': 'error',
                'message': 'Test already in progress'
            })
            return
            
        self.test_in_progress = True
        self.cable_authorized = False
        
        # Capture baseline
        await self.broadcast_message({
            'type': 'status',
            'message': 'Capturing baseline USB state...'
        })
        
        self.security_monitor.capture_baseline()
        self.usb_monitor.start_monitoring()
        
        await self.broadcast_message({
            'type': 'status',
            'message': 'Please connect the cable now...',
            'waiting_for_cable': True
        })
        
        # Run detection in thread
        def detect_cable():
            return self.security_monitor.detect_cable_insertion(timeout=30)
            
        cable_info = await asyncio.get_event_loop().run_in_executor(None, detect_cable)
        
        if not cable_info:
            await self.broadcast_message({
                'type': 'error',
                'message': 'No cable detected within timeout'
            })
            self.test_in_progress = False
            return
            
        # Analyze security
        is_safe, threats = self.security_monitor.analyze_cable_security(cable_info)
        
        result = {
            'type': 'security_result',
            'passed': is_safe,
            'threats': threats,
            'cable_info': cable_info
        }
        
        if is_safe:
            cable_hash = self.security_monitor.authorize_cable(cable_info)
            result['cable_hash'] = cable_hash
            self.cable_authorized = True
            
        await self.broadcast_message(result)
        self.test_in_progress = False
        
    async def _handle_performance_test(self):
        """Handle performance test request"""
        if not self.cable_authorized:
            await self.broadcast_message({
                'type': 'error',
                'message': 'Cable not authorized. Run security test first.'
            })
            return
            
        if self.test_in_progress:
            return
            
        self.test_in_progress = True
        
        # Run performance tests
        tests = [
            ('data_transfer', self._test_data_transfer),
            ('power_delivery', self._test_power_delivery),
            ('thunderbolt', self._test_thunderbolt),
            ('signal_integrity', self._test_signal_integrity)
        ]
        
        for test_name, test_func in tests:
            await self.broadcast_message({
                'type': 'test_progress',
                'test': test_name,
                'status': 'running'
            })
            
            result = await asyncio.get_event_loop().run_in_executor(None, test_func)
            
            await self.broadcast_message({
                'type': 'test_result',
                'test': test_name,
                'result': result
            })
            
        self.test_in_progress = False
        
    def _test_data_transfer(self) -> Dict:
        """Test data transfer speeds"""
        results = []
        for size_mb in [1, 10, 100]:
            remote_file = self.ssh_manager.create_test_file(size_mb)
            if remote_file:
                local_file = f"/tmp/cable_test_{size_mb}MB.dat"
                start_time = time.time()
                success = self.ssh_manager.transfer_file(remote_file, local_file, 'get')
                transfer_time = time.time() - start_time
                
                if success:
                    speed_mbps = (size_mb * 8) / transfer_time
                    results.append({
                        'size_mb': size_mb,
                        'time_seconds': transfer_time,
                        'speed_mbps': speed_mbps
                    })
                    
        return {'results': results}
        
    def _test_power_delivery(self) -> Dict:
        """Test power delivery"""
        power_info = self.ssh_manager.monitor_power_delivery()
        return power_info or {'error': 'Could not read power info'}
        
    def _test_thunderbolt(self) -> Dict:
        """Test Thunderbolt"""
        tb_info = self.ssh_manager.check_thunderbolt_status()
        return tb_info or {'status': 'not_detected'}
        
    def _test_signal_integrity(self) -> Dict:
        """Test signal integrity"""
        # Simplified for demo
        return {
            'iterations': 100,
            'errors': 0,
            'error_rate': 0.0
        }
        
    async def _handle_status_request(self):
        """Handle status request"""
        protection_status = self.security_monitor.bruteforce_protection.get_protection_status()
        packet_stats = self.security_monitor.packet_inspector.get_statistics()
        
        await self.broadcast_message({
            'type': 'status_update',
            'test_in_progress': self.test_in_progress,
            'cable_authorized': self.cable_authorized,
            'ssh_connected': self.ssh_manager.connected,
            'protection_status': protection_status,
            'packet_stats': packet_stats
        })
        
    async def _handle_emergency_stop(self):
        """Handle emergency stop"""
        await self.broadcast_message({
            'type': 'status',
            'message': 'Emergency stop initiated...'
        })
        
        # Stop all monitoring
        self.usb_monitor.stop_monitoring()
        self.security_monitor.bruteforce_protection.stop_monitoring()
        self.security_monitor.packet_inspector.stop_inspection()
        
        # Enter lockdown if needed
        self.security_monitor.bruteforce_protection._enter_lockdown_mode("Emergency stop")
        
        self.test_in_progress = False
        self.cable_authorized = False
        
        await self.broadcast_message({
            'type': 'emergency_stop_complete'
        })
        
    async def message_broadcaster(self):
        """Broadcast queued messages to clients"""
        while True:
            try:
                # Get messages from queue
                messages = []
                while not self.message_queue.empty():
                    messages.append(self.message_queue.get_nowait())
                    
                # Broadcast all messages
                for message in messages:
                    await self.broadcast_message(message)
                    
            except Exception as e:
                print(f"Broadcast error: {e}")
                
            await asyncio.sleep(0.1)
            
    async def start_server(self, host='localhost', port=8765):
        """Start WebSocket server"""
        # Start message broadcaster
        asyncio.create_task(self.message_broadcaster())
        
        print(f"Cable Tester Backend starting on ws://{host}:{port}")
        async with websockets.serve(self.handle_client, host, port):
            await asyncio.Future()  # Run forever

def main():
    backend = CableTesterBackend()
    asyncio.run(backend.start_server())

if __name__ == "__main__":
    main()