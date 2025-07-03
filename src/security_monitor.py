#!/usr/bin/env python3

import subprocess
import re
import time
import hashlib
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from bruteforce_protection import BruteForceProtection
from usb_packet_inspector import USBPacketInspector

class SecurityMonitor:
    def __init__(self):
        self.baseline_devices = {}
        self.bruteforce_protection = BruteForceProtection()
        self.packet_inspector = USBPacketInspector(self.bruteforce_protection)
        self.threat_signatures = {
            'hak5_omg': [
                'O.MG',
                'DuckyScript',
                'WiFi Duck',
                'KeyGrabber'
            ],
            'rubber_ducky': [
                'USB Rubber Ducky',
                'Bad USB',
                'Bash Bunny',
                'Key Croc'
            ],
            'suspicious_vid_pid': [
                ('0x05ac', '0x024f'),  # Suspicious Apple-like VID/PID
                ('0x03eb', '0x2ff4'),  # Known BadUSB VID/PID
            ],
            'suspicious_descriptors': [
                'HID Keyboard',
                'Mass Storage',
                'Network Adapter',
                'Serial Device'
            ]
        }
        self.authorized_cables = set()
        
    def capture_baseline(self) -> Dict:
        """Capture baseline USB device state before cable insertion"""
        # Start protection systems
        self.bruteforce_protection.start_monitoring()
        self.packet_inspector.start_inspection()
        
        baseline = {
            'timestamp': datetime.now().isoformat(),
            'devices': self._get_usb_devices(),
            'ioreg_snapshot': self._get_ioreg_snapshot(),
            'network_interfaces': self._get_network_interfaces()
        }
        self.baseline_devices = baseline
        return baseline
    
    def _get_usb_devices(self) -> List[Dict]:
        """Get current USB devices using system_profiler"""
        cmd = ['system_profiler', 'SPUSBDataType', '-json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return self._parse_usb_devices(data)
        return []
    
    def _parse_usb_devices(self, data: Dict) -> List[Dict]:
        """Parse USB device data from system_profiler"""
        devices = []
        
        def extract_devices(items):
            for item in items:
                if '_items' in item:
                    extract_devices(item['_items'])
                else:
                    device = {
                        'name': item.get('_name', 'Unknown'),
                        'vendor_id': item.get('vendor_id', ''),
                        'product_id': item.get('product_id', ''),
                        'manufacturer': item.get('manufacturer', ''),
                        'serial_number': item.get('serial_num', ''),
                        'location_id': item.get('location_id', ''),
                        'device_speed': item.get('device_speed', ''),
                        'bcd_device': item.get('bcd_device', '')
                    }
                    devices.append(device)
        
        if 'SPUSBDataType' in data:
            extract_devices(data['SPUSBDataType'])
        
        return devices
    
    def _get_ioreg_snapshot(self) -> str:
        """Get IORegistry snapshot for USB devices"""
        cmd = ['ioreg', '-r', '-c', 'IOUSBHostDevice', '-l']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else ""
    
    def _get_network_interfaces(self) -> List[str]:
        """Get list of network interfaces"""
        cmd = ['ifconfig', '-l']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip().split() if result.returncode == 0 else []
    
    def detect_cable_insertion(self, timeout: int = 30) -> Optional[Dict]:
        """Monitor for cable insertion with timeout"""
        print(f"Monitoring for cable insertion (timeout: {timeout}s)...")
        start_time = time.time()
        enumeration_count = 0
        last_device_count = len(self.baseline_devices.get('devices', []))
        
        while time.time() - start_time < timeout:
            # Check if in lockdown mode
            if self.bruteforce_protection.lockdown_mode:
                print("\n🚨 System in lockdown mode - cable testing suspended")
                return None
                
            current_devices = self._get_usb_devices()
            
            # Track enumeration attempts
            if len(current_devices) != last_device_count:
                enumeration_count += 1
                self.bruteforce_protection.record_enumeration(f"enum_{enumeration_count}")
                last_device_count = len(current_devices)
            
            # Check for new devices
            baseline_ids = {(d['vendor_id'], d['product_id'], d['location_id']) 
                           for d in self.baseline_devices.get('devices', [])}
            current_ids = {(d['vendor_id'], d['product_id'], d['location_id']) 
                          for d in current_devices}
            
            new_devices = current_ids - baseline_ids
            
            if new_devices:
                # Found new device(s)
                new_device_info = []
                for device in current_devices:
                    device_id = (device['vendor_id'], device['product_id'], device['location_id'])
                    if device_id in new_devices:
                        # Check if device is blocked
                        device_hash = f"{device['vendor_id']}:{device['product_id']}"
                        if self.bruteforce_protection.is_device_blocked(device_hash):
                            print(f"\n⛔ Blocked device detected: {device_hash}")
                            continue
                            
                        new_device_info.append(device)
                
                if new_device_info:
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'new_devices': new_device_info,
                        'all_devices': current_devices
                    }
            
            time.sleep(0.5)
        
        return None
    
    def analyze_cable_security(self, cable_info: Dict) -> Tuple[bool, List[str]]:
        """Analyze cable for security threats"""
        threats_found = []
        
        # Check brute-force protection status first
        protection_status = self.bruteforce_protection.get_protection_status()
        if protection_status['lockdown_mode']:
            threats_found.append("System in lockdown mode due to attack")
            return False, threats_found
            
        # Check packet inspection results
        packet_stats = self.packet_inspector.get_statistics()
        if packet_stats['suspicious_packets'] > 0:
            threats_found.append(f"Suspicious USB packets detected: {packet_stats['suspicious_packets']}")
            for pattern, count in packet_stats['pattern_matches'].items():
                if count > 0:
                    threats_found.append(f"  - {pattern}: {count} matches")
        
        for device in cable_info.get('new_devices', []):
            device_id = f"{device.get('vendor_id', '')}:{device.get('product_id', '')}"
            
            # Check if device is blocked
            if self.bruteforce_protection.is_device_blocked(device_id):
                threats_found.append(f"Device {device_id} is blocked due to previous attacks")
                continue
                
            # Record device for tracking
            self.bruteforce_protection.record_reconnection(device_id)
            
            # Check device name against known threats
            device_name = str(device.get('name', '')).lower()
            for threat_type, signatures in self.threat_signatures.items():
                # Skip non-string signature types (like VID/PID tuples)
                if threat_type == 'suspicious_vid_pid':
                    continue
                for signature in signatures:
                    if str(signature).lower() in device_name:
                        threats_found.append(f"Potential {threat_type} detected: {signature}")
            
            # Check VID/PID combinations
            vid = device.get('vendor_id', '')
            pid = device.get('product_id', '')
            for sus_vid, sus_pid in self.threat_signatures['suspicious_vid_pid']:
                if vid == sus_vid and pid == sus_pid:
                    threats_found.append(f"Suspicious VID/PID combination: {vid}:{pid}")
            
            # Check for multiple device functions (common in malicious cables)
            if self._check_multiple_functions(device):
                threats_found.append("Multiple device functions detected (potential BadUSB)")
                
            # Track descriptor changes
            self.bruteforce_protection.record_descriptor_change(device_id, device)
        
        # Check for unexpected network interfaces
        new_interfaces = self._check_new_network_interfaces()
        if new_interfaces:
            threats_found.append(f"New network interfaces detected: {new_interfaces}")
        
        # Check IORegistry for suspicious entries
        suspicious_ioreg = self._check_ioreg_anomalies()
        if suspicious_ioreg:
            threats_found.extend(suspicious_ioreg)
        
        is_safe = len(threats_found) == 0
        return is_safe, threats_found
    
    def _check_multiple_functions(self, device: Dict) -> bool:
        """Check if device presents multiple functions"""
        # This would need more detailed USB descriptor analysis
        # For now, checking if device name suggests multiple functions
        name = device.get('name', '').lower()
        function_keywords = ['composite', 'multifunction', 'hub']
        return any(keyword in name for keyword in function_keywords)
    
    def _check_new_network_interfaces(self) -> List[str]:
        """Check for new network interfaces"""
        current_interfaces = self._get_network_interfaces()
        baseline_interfaces = self.baseline_devices.get('network_interfaces', [])
        return list(set(current_interfaces) - set(baseline_interfaces))
    
    def _check_ioreg_anomalies(self) -> List[str]:
        """Check IORegistry for suspicious entries"""
        anomalies = []
        current_ioreg = self._get_ioreg_snapshot()
        
        # Look for suspicious patterns
        suspicious_patterns = [
            r'kUSBDeviceClass.*?= 0x09',  # USB Hub class
            r'USB Product Name.*?HID',      # HID devices
            r'bDeviceClass.*?= 0xe0',       # Wireless controller
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, current_ioreg):
                anomalies.append(f"Suspicious IORegistry pattern detected: {pattern}")
        
        return anomalies
    
    def authorize_cable(self, cable_info: Dict) -> str:
        """Generate authorization token for safe cable"""
        cable_hash = hashlib.sha256(
            json.dumps(cable_info, sort_keys=True).encode()
        ).hexdigest()
        
        authorization = {
            'cable_hash': cable_hash,
            'authorized_at': datetime.now().isoformat(),
            'devices': cable_info.get('new_devices', [])
        }
        
        self.authorized_cables.add(cable_hash)
        return cable_hash
    
    def is_cable_authorized(self, cable_hash: str) -> bool:
        """Check if cable is authorized"""
        return cable_hash in self.authorized_cables