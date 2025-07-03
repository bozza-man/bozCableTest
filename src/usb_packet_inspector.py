#!/usr/bin/env python3

import subprocess
import threading
import time
import struct
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime

class USBPacketInspector:
    def __init__(self, bruteforce_protection=None):
        self.bruteforce_protection = bruteforce_protection
        self.packet_queue = deque(maxlen=10000)
        self.suspicious_patterns = {
            # HID attack patterns
            'hid_flood': {
                'pattern': b'\x00\x00',  # Repeated null HID reports
                'threshold': 100,
                'window': 1.0
            },
            'keyboard_injection': {
                'pattern': b'\x02\x00',  # Keyboard modifier keys
                'threshold': 50,
                'window': 0.5
            },
            # Mass storage attacks
            'storage_probe': {
                'pattern': b'\x55\x53\x42\x43',  # USBC signature
                'threshold': 200,
                'window': 2.0
            },
            # Network attacks
            'rndis_flood': {
                'pattern': b'RNDIS',
                'threshold': 100,
                'window': 1.0
            },
            # DMA patterns
            'thunderbolt_dma': {
                'pattern': b'\x87\x83',  # TB3 config space
                'threshold': 10,
                'window': 0.1
            }
        }
        
        self.packet_stats = {
            'total_packets': 0,
            'suspicious_packets': 0,
            'blocked_packets': 0,
            'pattern_matches': {}
        }
        
        self.monitoring = False
        self.pcap_process = None
        
    def start_inspection(self, device_id: Optional[str] = None):
        """Start USB packet inspection"""
        self.monitoring = True
        
        # Start USB packet capture
        self._start_packet_capture(device_id)
        
        # Start analysis thread
        analysis_thread = threading.Thread(target=self._analyze_packets)
        analysis_thread.daemon = True
        analysis_thread.start()
        
    def stop_inspection(self):
        """Stop packet inspection"""
        self.monitoring = False
        
        if self.pcap_process:
            self.pcap_process.terminate()
            self.pcap_process = None
            
    def _start_packet_capture(self, device_id: Optional[str]):
        """Start capturing USB packets"""
        try:
            # Use system tools to capture USB traffic
            # On macOS, we can use ioreg and fs_usage for USB monitoring
            cmd = [
                'sudo', 'fs_usage', '-w', '-f', 'filesys',
                'kernel_task'
            ]
            
            self.pcap_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Start packet reader thread
            reader_thread = threading.Thread(target=self._read_packets)
            reader_thread.daemon = True
            reader_thread.start()
            
        except Exception as e:
            print(f"Failed to start packet capture: {e}")
            
    def _read_packets(self):
        """Read packets from capture process"""
        if not self.pcap_process:
            return
            
        for line in self.pcap_process.stdout:
            if 'USB' in line or 'IOUSBHostDevice' in line:
                self._process_raw_packet(line)
                
    def _process_raw_packet(self, raw_data: str):
        """Process raw packet data"""
        try:
            # Extract relevant USB data
            packet = {
                'timestamp': time.time(),
                'raw': raw_data,
                'data': self._extract_usb_data(raw_data)
            }
            
            self.packet_queue.append(packet)
            self.packet_stats['total_packets'] += 1
            
        except Exception as e:
            pass
            
    def _extract_usb_data(self, raw_data: str) -> bytes:
        """Extract USB data from raw capture"""
        # This is simplified - real implementation would parse USB packets
        # For now, we'll simulate by looking for hex patterns
        hex_pattern = b''
        
        # Look for hex data in the output
        parts = raw_data.split()
        for part in parts:
            if len(part) == 2 and all(c in '0123456789ABCDEFabcdef' for c in part):
                try:
                    hex_pattern += bytes.fromhex(part)
                except:
                    pass
                    
        return hex_pattern
        
    def _analyze_packets(self):
        """Analyze packets for suspicious patterns"""
        pattern_windows = {name: deque() for name in self.suspicious_patterns}
        
        while self.monitoring:
            try:
                # Process packets in queue
                while self.packet_queue:
                    packet = self.packet_queue.popleft()
                    self._check_packet_patterns(packet, pattern_windows)
                    
                # Check for attack patterns
                self._detect_attacks(pattern_windows)
                
                time.sleep(0.01)  # 10ms analysis interval
                
            except Exception as e:
                print(f"Packet analysis error: {e}")
                
    def _check_packet_patterns(self, packet: Dict, pattern_windows: Dict):
        """Check packet against known patterns"""
        packet_data = packet.get('data', b'')
        timestamp = packet['timestamp']
        
        for pattern_name, pattern_info in self.suspicious_patterns.items():
            pattern = pattern_info['pattern']
            
            if pattern in packet_data:
                # Add to pattern window
                pattern_windows[pattern_name].append(timestamp)
                
                # Track pattern matches
                if pattern_name not in self.packet_stats['pattern_matches']:
                    self.packet_stats['pattern_matches'][pattern_name] = 0
                self.packet_stats['pattern_matches'][pattern_name] += 1
                
    def _detect_attacks(self, pattern_windows: Dict):
        """Detect attacks based on pattern analysis"""
        current_time = time.time()
        
        for pattern_name, timestamps in pattern_windows.items():
            pattern_info = self.suspicious_patterns[pattern_name]
            window = pattern_info['window']
            threshold = pattern_info['threshold']
            
            # Remove old timestamps
            while timestamps and current_time - timestamps[0] > window:
                timestamps.popleft()
                
            # Check if threshold exceeded
            if len(timestamps) > threshold:
                self._handle_pattern_attack(pattern_name, len(timestamps))
                
                # Clear the window to prevent repeated alerts
                timestamps.clear()
                
    def _handle_pattern_attack(self, pattern_name: str, count: int):
        """Handle detected pattern attack"""
        self.packet_stats['suspicious_packets'] += count
        
        print(f"\n⚠️  USB Pattern Attack Detected: {pattern_name}")
        print(f"   Count: {count} packets")
        
        # Notify bruteforce protection
        if self.bruteforce_protection:
            if pattern_name == 'hid_flood':
                self.bruteforce_protection._log_attack(
                    "HID Flood Attack", 
                    f"{count} HID packets"
                )
            elif pattern_name == 'keyboard_injection':
                self.bruteforce_protection._log_attack(
                    "Keyboard Injection Attack",
                    f"{count} keyboard packets"
                )
            elif pattern_name == 'thunderbolt_dma':
                self.bruteforce_protection._log_attack(
                    "Thunderbolt DMA Attempt",
                    f"{count} DMA packets"
                )
                # Critical - immediate lockdown
                self.bruteforce_protection._enter_lockdown_mode(
                    "Thunderbolt DMA attack detected"
                )
                
    def inject_test_pattern(self, pattern_name: str, count: int):
        """Inject test pattern for testing (demo only)"""
        if pattern_name not in self.suspicious_patterns:
            return
            
        pattern_info = self.suspicious_patterns[pattern_name]
        pattern = pattern_info['pattern']
        
        # Simulate packet injection
        for i in range(count):
            packet = {
                'timestamp': time.time(),
                'raw': f'TEST: {pattern_name}',
                'data': pattern + b'\x00' * 10
            }
            self.packet_queue.append(packet)
            time.sleep(0.001)  # Small delay between packets
            
    def get_statistics(self) -> Dict:
        """Get packet inspection statistics"""
        return {
            'total_packets': self.packet_stats['total_packets'],
            'suspicious_packets': self.packet_stats['suspicious_packets'],
            'blocked_packets': self.packet_stats['blocked_packets'],
            'pattern_matches': self.packet_stats['pattern_matches'].copy(),
            'queue_size': len(self.packet_queue)
        }
        
    def block_device_packets(self, device_id: str):
        """Block all packets from specific device"""
        print(f"🛡️  Blocking all packets from device: {device_id}")
        # This would integrate with kernel-level filtering
        
    def set_pattern_threshold(self, pattern_name: str, threshold: int):
        """Adjust pattern detection threshold"""
        if pattern_name in self.suspicious_patterns:
            self.suspicious_patterns[pattern_name]['threshold'] = threshold