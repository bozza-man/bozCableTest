#!/usr/bin/env python3

import subprocess
import json
import threading
import time
import queue
from typing import Dict, List, Callable, Optional
from datetime import datetime
from enum import Enum

class USBEvent(Enum):
    DEVICE_ADDED = "device_added"
    DEVICE_REMOVED = "device_removed"
    DEVICE_CHANGED = "device_changed"
    ENUMERATION_FAILED = "enumeration_failed"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

class USBMonitor:
    def __init__(self, security_monitor=None):
        self.monitoring = False
        self.monitor_thread = None
        self.event_queue = queue.Queue()
        self.event_handlers = {}
        self.device_cache = {}
        self.security_monitor = security_monitor
        self.enumeration_attempts = {}
        self.suspicious_patterns = {
            'rapid_reconnect': [],  # Track rapid reconnections
            'multiple_descriptors': [],  # Track descriptor changes
            'vid_pid_changes': []  # Track VID/PID changes
        }
        
    def start_monitoring(self):
        """Start USB monitoring thread"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Start event processor
        self.event_thread = threading.Thread(target=self._process_events)
        self.event_thread.daemon = True
        self.event_thread.start()
    
    def stop_monitoring(self):
        """Stop USB monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def register_handler(self, event_type: USBEvent, handler: Callable):
        """Register event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        poll_interval = 0.5  # 500ms polling
        
        while self.monitoring:
            try:
                current_devices = self._get_current_devices()
                self._detect_changes(current_devices)
                time.sleep(poll_interval)
            except Exception as e:
                # Monitor error - silently continue
                time.sleep(1)
    
    def _get_current_devices(self) -> Dict:
        """Get current USB device state"""
        devices = {}
        
        # Try system_profiler first
        try:
            result = subprocess.run(
                ['system_profiler', 'SPUSBDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                devices = self._parse_device_tree(data)
                
        except subprocess.TimeoutExpired:
            # Possible enumeration hang
            self._handle_enumeration_timeout()
        except Exception as e:
            # Failed to get USB devices via system_profiler
            pass
        
        # If no devices found, try ioreg as fallback
        if len(devices) == 0:
            devices = self._get_devices_via_ioreg()
        
        # Always populate with basic USB device info if still empty
        if len(devices) == 0:
            devices = self._get_basic_usb_devices()
            
        return devices
    
    def _parse_device_tree(self, data: Dict) -> Dict:
        """Parse USB device tree into flat dictionary"""
        devices = {}
        
        def parse_items(items, parent_path=""):
            for item in items:
                if '_items' in item:
                    # This is a hub/controller
                    hub_name = item.get('_name', 'Unknown')
                    parse_items(item['_items'], f"{parent_path}/{hub_name}")
                else:
                    # This is a device
                    device_id = self._generate_device_id(item)
                    device_info = {
                        'name': item.get('_name', 'Unknown'),
                        'vendor_id': item.get('vendor_id', ''),
                        'product_id': item.get('product_id', ''),
                        'serial_number': item.get('serial_num', ''),
                        'manufacturer': item.get('manufacturer', ''),
                        'location_id': item.get('location_id', ''),
                        'device_speed': item.get('device_speed', ''),
                        'current_required': item.get('current_required', ''),
                        'extra_current_used': item.get('extra_current_used', ''),
                        'bcd_device': item.get('bcd_device', ''),
                        'path': parent_path,
                        'raw_data': item
                    }
                    devices[device_id] = device_info
        
        # Handle USB data format
        if 'SPUSBDataType' in data:
            # DEBUG: Found USB root items
            for root_item in data['SPUSBDataType']:
                if '_items' in root_item:
                    # This is a USB controller/hub with devices
                    parse_items(root_item['_items'], root_item.get('_name', 'Root'))
                else:
                    # Some devices might be at root level
                    device_id = self._generate_device_id(root_item)
                    if device_id and device_id != ':::':  # Skip empty devices
                        device_info = {
                            'name': root_item.get('_name', 'Unknown'),
                            'vendor_id': root_item.get('vendor_id', ''),
                            'product_id': root_item.get('product_id', ''),
                            'serial_number': root_item.get('serial_num', ''),
                            'manufacturer': root_item.get('manufacturer', ''),
                            'location_id': root_item.get('location_id', ''),
                            'device_speed': root_item.get('device_speed', ''),
                            'current_required': root_item.get('current_required', ''),
                            'extra_current_used': root_item.get('extra_current_used', ''),
                            'bcd_device': root_item.get('bcd_device', ''),
                            'path': 'Root',
                            'raw_data': root_item
                        }
                        devices[device_id] = device_info
        else:
            # DEBUG: No SPUSBDataType found in data
            pass
        
        # DEBUG: Parsed devices
        return devices
    
    def _get_devices_via_ioreg(self) -> Dict:
        """Get USB devices via ioreg as fallback"""
        devices = {}
        try:
            result = subprocess.run(
                ['ioreg', '-p', 'IOUSB', '-l'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Parse ioreg output
                current_device = {}
                for line in result.stdout.split('\n'):
                    if '<class IOUSBHostDevice' in line:
                        # New device found
                        if current_device and 'name' in current_device:
                            device_id = self._generate_device_id(current_device)
                            if device_id != ':::':
                                devices[device_id] = current_device
                        current_device = {}
                        # Extract device name from line
                        if '@' in line:
                            name = line.split('@')[0].split()[-1]
                            current_device['name'] = str(name)
                    elif '"' in line and '=' in line and current_device is not None:
                        # Parse device properties
                        parts = line.strip().split('=', 1)
                        if len(parts) == 2:
                            key = parts[0].strip().strip('"')
                            value = parts[1].strip().strip('"')
                            
                            # Map ioreg keys to our format
                            if key == 'idVendor':
                                current_device['vendor_id'] = hex(int(value))
                            elif key == 'idProduct':
                                current_device['product_id'] = hex(int(value))
                            elif key == 'USB Serial Number':
                                current_device['serial_number'] = value
                            elif key == 'USB Vendor Name':
                                current_device['manufacturer'] = value
                            elif key == 'locationID':
                                current_device['location_id'] = hex(int(value))
                            elif key == 'USB Speed':
                                current_device['device_speed'] = value
                
                # Don't forget the last device
                if current_device and 'name' in current_device:
                    device_id = self._generate_device_id(current_device)
                    if device_id != ':::':
                        devices[device_id] = current_device
                        
                # DEBUG: ioreg found devices
                
        except Exception as e:
            # Failed to get USB devices via ioreg
            pass
            
        return devices
    
    def _get_basic_usb_devices(self) -> Dict:
        """Get basic USB device list using simple ioreg parsing"""
        devices = {}
        try:
            # Get simple list of USB devices
            result = subprocess.run(
                ['ioreg', '-p', 'IOUSB', '-w0'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                device_count = 0
                
                for line in lines:
                    if '<class IOUSBHostDevice' in line and '@' in line:
                        # Extract device name
                        parts = line.split('@')
                        if len(parts) >= 2:
                            name_part = parts[0].strip().split()[-1]
                            location = parts[1].split()[0]
                            
                            device_count += 1
                            device_id = f"usb_device_{device_count}"
                            
                            devices[device_id] = {
                                'name': name_part,
                                'location_id': location,
                                'vendor_id': '0x0000',
                                'product_id': '0x0000',
                                'manufacturer': 'Unknown',
                                'device_speed': 'Unknown',
                                'raw_data': {'line': line}
                            }
                            # DEBUG: Found USB device
                            pass
                
                # DEBUG: Basic scan found USB devices
                
        except Exception as e:
            # Failed basic USB scan
            pass
            
        return devices
    
    def _generate_device_id(self, device: Dict) -> str:
        """Generate unique device ID"""
        # Use combination of VID, PID, serial, and location
        vid = device.get('vendor_id', '')
        pid = device.get('product_id', '')
        serial = device.get('serial_num', device.get('serial_number', ''))
        location = device.get('location_id', '')
        
        # If we have a name but no other info, use the name as part of the ID
        if not vid and not pid and not location:
            name = device.get('name', 'unknown')
            return f"device_{name}_{id(device)}"
        
        return f"{vid}:{pid}:{serial}:{location}"
    
    def _detect_changes(self, current_devices: Dict):
        """Detect changes in USB devices"""
        current_ids = set(current_devices.keys())
        cached_ids = set(self.device_cache.keys())
        
        # New devices
        added_ids = current_ids - cached_ids
        for device_id in added_ids:
            device = current_devices[device_id]
            self._handle_device_added(device_id, device)
        
        # Removed devices
        removed_ids = cached_ids - current_ids
        for device_id in removed_ids:
            device = self.device_cache[device_id]
            self._handle_device_removed(device_id, device)
        
        # Changed devices
        for device_id in current_ids & cached_ids:
            if self._device_changed(self.device_cache[device_id], current_devices[device_id]):
                self._handle_device_changed(device_id, current_devices[device_id])
        
        # Update cache
        self.device_cache = current_devices
    
    def _device_changed(self, old_device: Dict, new_device: Dict) -> bool:
        """Check if device properties changed"""
        # Check key properties
        check_fields = ['name', 'device_speed', 'current_required', 'extra_current_used']
        
        for field in check_fields:
            if old_device.get(field) != new_device.get(field):
                return True
        
        return False
    
    def _handle_device_added(self, device_id: str, device: Dict):
        """Handle device addition"""
        timestamp = datetime.now()
        
        # Check for rapid reconnections
        self._check_rapid_reconnect(device)
        
        # Check for suspicious characteristics
        threats = self._analyze_device_threats(device)
        
        if threats:
            event = {
                'type': USBEvent.SUSPICIOUS_ACTIVITY,
                'device_id': device_id,
                'device': device,
                'threats': threats,
                'timestamp': timestamp
            }
        else:
            event = {
                'type': USBEvent.DEVICE_ADDED,
                'device_id': device_id,
                'device': device,
                'timestamp': timestamp
            }
        
        self.event_queue.put(event)
    
    def _handle_device_removed(self, device_id: str, device: Dict):
        """Handle device removal"""
        event = {
            'type': USBEvent.DEVICE_REMOVED,
            'device_id': device_id,
            'device': device,
            'timestamp': datetime.now()
        }
        self.event_queue.put(event)
    
    def _handle_device_changed(self, device_id: str, device: Dict):
        """Handle device change"""
        # Track descriptor changes
        self.suspicious_patterns['multiple_descriptors'].append({
            'device_id': device_id,
            'timestamp': datetime.now()
        })
        
        event = {
            'type': USBEvent.DEVICE_CHANGED,
            'device_id': device_id,
            'device': device,
            'timestamp': datetime.now()
        }
        self.event_queue.put(event)
    
    def _handle_enumeration_timeout(self):
        """Handle enumeration timeout (possible attack)"""
        event = {
            'type': USBEvent.ENUMERATION_FAILED,
            'message': 'USB enumeration timeout detected',
            'timestamp': datetime.now()
        }
        self.event_queue.put(event)
    
    def _check_rapid_reconnect(self, device: Dict):
        """Check for rapid reconnection patterns"""
        device_key = f"{device.get('vendor_id', 'unknown')}:{device.get('product_id', 'unknown')}"
        now = datetime.now()
        
        # Clean old entries
        self.suspicious_patterns['rapid_reconnect'] = [
            entry for entry in self.suspicious_patterns['rapid_reconnect']
            if (now - entry['timestamp']).total_seconds() < 10
        ]
        
        # Add new entry
        self.suspicious_patterns['rapid_reconnect'].append({
            'device_key': device_key,
            'timestamp': now
        })
        
        # Check if too many reconnects
        device_reconnects = [
            entry for entry in self.suspicious_patterns['rapid_reconnect']
            if entry['device_key'] == device_key
        ]
        
        if len(device_reconnects) > 3:
            return True
        
        return False
    
    def _analyze_device_threats(self, device: Dict) -> List[str]:
        """Analyze device for threats"""
        threats = []
        
        # Check device name
        suspicious_names = ['HID', 'Keyboard', 'BadUSB', 'Rubber', 'Ducky']
        device_name = str(device.get('name', '')).lower()
        for name in suspicious_names:
            if name.lower() in device_name:
                threats.append(f"Suspicious device name: {name}")
        
        # Check for HID class in non-HID device
        if 'HID' in str(device.get('name', '')) and 'cable' in device_name:
            threats.append("HID functionality in cable device")
        
        # Check for unusual power requirements
        current = device.get('current_required', '0')
        if current:
            try:
                current_ma = int(current.replace('mA', '').strip())
                if current_ma > 900:  # USB 3.0 max is 900mA
                    threats.append(f"Excessive power requirement: {current_ma}mA")
            except:
                pass
        
        # Use security monitor if available
        if self.security_monitor:
            is_safe, security_threats = self.security_monitor.analyze_cable_security(
                {'new_devices': [device]}
            )
            if not is_safe:
                threats.extend(security_threats)
        
        return threats
    
    def _process_events(self):
        """Process events from queue"""
        while self.monitoring:
            try:
                event = self.event_queue.get(timeout=1)
                event_type = event['type']
                
                # Call registered handlers
                if event_type in self.event_handlers:
                    for handler in self.event_handlers[event_type]:
                        try:
                            handler(event)
                        except Exception as e:
                            print(f"Handler error: {e}")
                            
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Event processing error: {e}")
    
    def get_current_state(self) -> Dict:
        """Get current USB state snapshot"""
        return {
            'devices': self.device_cache.copy(),
            'suspicious_patterns': self.suspicious_patterns.copy(),
            'timestamp': datetime.now().isoformat()
        }
    
    def is_device_authorized(self, device_id: str) -> bool:
        """Check if device is authorized"""
        if self.security_monitor:
            device = self.device_cache.get(device_id)
            if device:
                cable_hash = self.security_monitor.authorize_cable(
                    {'new_devices': [device]}
                )
                return self.security_monitor.is_cable_authorized(cable_hash)
        
        return False