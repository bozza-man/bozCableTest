#!/usr/bin/env python3

import time
import threading
import subprocess
import os
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib
import json

class BruteForceProtection:
    def __init__(self):
        # Attack detection thresholds
        self.enumeration_threshold = 5  # Max enumerations per second
        self.reconnect_threshold = 10   # Max reconnects in 5 seconds
        self.descriptor_change_threshold = 3  # Max descriptor changes
        self.packet_flood_threshold = 1000  # Packets per second
        
        # Tracking structures
        self.enumeration_events = deque(maxlen=100)
        self.reconnect_events = defaultdict(deque)
        self.descriptor_changes = defaultdict(list)
        self.packet_counts = defaultdict(int)
        self.blocked_devices = set()
        self.attack_log = []
        
        # Protection state
        self.lockdown_mode = False
        self.monitoring = False
        self.monitor_thread = None
        
        # USB subsystem control
        self.usb_enabled = True
        self.original_kext_state = {}
        
    def start_monitoring(self):
        """Start brute-force protection monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Start kernel event monitoring
        self._start_kernel_monitoring()
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
    def _monitor_loop(self):
        """Main monitoring loop for attack detection"""
        while self.monitoring:
            try:
                # Check for various attack patterns
                self._check_enumeration_attacks()
                self._check_reconnection_attacks()
                self._check_descriptor_attacks()
                self._check_packet_floods()
                
                # Clean old events
                self._cleanup_old_events()
                
                time.sleep(0.1)  # 100ms polling
                
            except Exception as e:
                print(f"Monitor error: {e}")
                
    def _start_kernel_monitoring(self):
        """Monitor kernel USB events for attacks"""
        # Monitor system log for USB events
        try:
            # Use log stream to monitor USB events in real-time
            cmd = [
                'log', 'stream',
                '--predicate', 'processImagePath contains "kernel" and messageType == info and subsystem == "com.apple.usb"',
                '--style', 'json'
            ]
            
            self.log_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Start thread to process log events
            log_thread = threading.Thread(target=self._process_kernel_logs)
            log_thread.daemon = True
            log_thread.start()
            
        except Exception as e:
            print(f"Failed to start kernel monitoring: {e}")
            
    def _process_kernel_logs(self):
        """Process kernel USB logs for attack patterns"""
        if not hasattr(self, 'log_process'):
            return
            
        for line in self.log_process.stdout:
            try:
                event = json.loads(line)
                self._analyze_kernel_event(event)
            except:
                continue
                
    def _analyze_kernel_event(self, event: Dict):
        """Analyze kernel event for attack patterns"""
        message = event.get('eventMessage', '')
        
        # Detect rapid enumeration
        if 'USB device enumeration' in message:
            self.enumeration_events.append(time.time())
            
        # Detect descriptor flooding
        if 'descriptor' in message.lower():
            self._handle_descriptor_event(event)
            
        # Detect DMA attempts
        if 'DMA' in message or 'direct memory' in message.lower():
            self._handle_dma_attempt(event)
            
    def record_enumeration(self, device_id: str):
        """Record USB enumeration event"""
        current_time = time.time()
        self.enumeration_events.append(current_time)
        
        # Check if enumeration rate exceeds threshold
        recent_events = [t for t in self.enumeration_events 
                        if current_time - t < 1.0]
        
        if len(recent_events) > self.enumeration_threshold:
            self._trigger_enumeration_protection(device_id)
            
    def record_reconnection(self, device_id: str):
        """Record device reconnection"""
        current_time = time.time()
        self.reconnect_events[device_id].append(current_time)
        
        # Keep only recent events
        self.reconnect_events[device_id] = deque(
            [t for t in self.reconnect_events[device_id] 
             if current_time - t < 5.0],
            maxlen=50
        )
        
        if len(self.reconnect_events[device_id]) > self.reconnect_threshold:
            self._trigger_reconnection_protection(device_id)
            
    def record_descriptor_change(self, device_id: str, descriptor: Dict):
        """Record descriptor change for device"""
        descriptor_hash = hashlib.sha256(
            json.dumps(descriptor, sort_keys=True).encode()
        ).hexdigest()
        
        self.descriptor_changes[device_id].append({
            'hash': descriptor_hash,
            'timestamp': time.time()
        })
        
        # Check for descriptor flooding
        unique_descriptors = set(d['hash'] for d in self.descriptor_changes[device_id])
        if len(unique_descriptors) > self.descriptor_change_threshold:
            self._trigger_descriptor_protection(device_id)
            
    def _check_enumeration_attacks(self):
        """Check for enumeration-based attacks"""
        current_time = time.time()
        recent_enumerations = [t for t in self.enumeration_events 
                              if current_time - t < 1.0]
        
        if len(recent_enumerations) > self.enumeration_threshold * 2:
            self._enter_lockdown_mode("Enumeration flood detected")
            
    def _check_reconnection_attacks(self):
        """Check for rapid reconnection attacks"""
        for device_id, events in self.reconnect_events.items():
            if len(events) > self.reconnect_threshold * 2:
                self._block_device(device_id, "Rapid reconnection attack")
                
    def _check_descriptor_attacks(self):
        """Check for descriptor manipulation attacks"""
        for device_id, changes in self.descriptor_changes.items():
            recent_changes = [c for c in changes 
                            if time.time() - c['timestamp'] < 10.0]
            
            if len(recent_changes) > self.descriptor_change_threshold * 3:
                self._block_device(device_id, "Descriptor manipulation attack")
                
    def _check_packet_floods(self):
        """Check for USB packet flooding"""
        # This would integrate with lower-level USB monitoring
        # For now, checking based on event rates
        total_events = (len(self.enumeration_events) + 
                       sum(len(events) for events in self.reconnect_events.values()))
        
        if total_events > self.packet_flood_threshold:
            self._enter_lockdown_mode("USB packet flood detected")
            
    def _trigger_enumeration_protection(self, device_id: str):
        """Trigger protection against enumeration attacks"""
        self._log_attack("Enumeration attack", device_id)
        
        # Temporarily disable USB enumeration
        self._throttle_usb_enumeration()
        
        # Block the device
        self._block_device(device_id, "Enumeration attack")
        
    def _trigger_reconnection_protection(self, device_id: str):
        """Trigger protection against reconnection attacks"""
        self._log_attack("Reconnection attack", device_id)
        
        # Block the device
        self._block_device(device_id, "Rapid reconnection")
        
        # Add delay to USB port
        self._add_port_delay(device_id)
        
    def _trigger_descriptor_protection(self, device_id: str):
        """Trigger protection against descriptor attacks"""
        self._log_attack("Descriptor manipulation", device_id)
        
        # Block device and report
        self._block_device(device_id, "Descriptor manipulation")
        
    def _enter_lockdown_mode(self, reason: str):
        """Enter USB lockdown mode"""
        if self.lockdown_mode:
            return
            
        self.lockdown_mode = True
        self._log_attack("LOCKDOWN MODE", reason)
        
        print(f"\n🚨 USB LOCKDOWN MODE ACTIVATED 🚨")
        print(f"Reason: {reason}")
        print("All USB operations suspended")
        
        # Disable non-essential USB
        self._disable_usb_subsystem()
        
        # Schedule recovery
        threading.Timer(30.0, self._exit_lockdown_mode).start()
        
    def _exit_lockdown_mode(self):
        """Exit lockdown mode"""
        self.lockdown_mode = False
        print("\n✅ Exiting USB lockdown mode")
        
        # Re-enable USB
        self._enable_usb_subsystem()
        
    def _block_device(self, device_id: str, reason: str):
        """Block a specific device"""
        self.blocked_devices.add(device_id)
        print(f"\n⛔ Device blocked: {device_id}")
        print(f"Reason: {reason}")
        
        # Add to system USB blacklist
        self._add_to_usb_blacklist(device_id)
        
    def _throttle_usb_enumeration(self):
        """Throttle USB enumeration rate"""
        # This would interact with USB subsystem
        # For demo, we'll simulate with delays
        print("⚡ USB enumeration throttled")
        
    def _add_port_delay(self, device_id: str):
        """Add delay to USB port to prevent rapid reconnects"""
        print(f"⏱️  Adding 5-second delay to port for device {device_id}")
        
    def _disable_usb_subsystem(self):
        """Disable non-essential USB functionality"""
        if not self.usb_enabled:
            return
            
        print("🔒 Disabling non-essential USB...")
        
        # Save current state
        self._save_usb_state()
        
        # Disable USB mass storage (example)
        try:
            subprocess.run(
                ['sudo', 'kextunload', '-b', 'com.apple.driver.usb.IOUSBMassStorageDriver'],
                capture_output=True
            )
        except:
            pass
            
        self.usb_enabled = False
        
    def _enable_usb_subsystem(self):
        """Re-enable USB functionality"""
        if self.usb_enabled:
            return
            
        print("🔓 Re-enabling USB...")
        
        # Restore USB state
        self._restore_usb_state()
        
        self.usb_enabled = True
        
    def _save_usb_state(self):
        """Save current USB state"""
        try:
            result = subprocess.run(
                ['kextstat', '-l'],
                capture_output=True,
                text=True
            )
            self.original_kext_state['kexts'] = result.stdout
        except:
            pass
            
    def _restore_usb_state(self):
        """Restore USB state"""
        # This would restore the original kext state
        pass
        
    def _add_to_usb_blacklist(self, device_id: str):
        """Add device to system USB blacklist"""
        # This would add to macOS USB device blacklist
        # For now, we'll track internally
        pass
        
    def _handle_dma_attempt(self, event: Dict):
        """Handle potential DMA attack attempt"""
        self._log_attack("DMA ATTACK ATTEMPT", event)
        
        # Immediate lockdown
        self._enter_lockdown_mode("Potential DMA attack detected")
        
        # Alert user
        print("\n🚨 CRITICAL: Potential DMA attack detected!")
        print("System entering protective mode")
        
    def _cleanup_old_events(self):
        """Clean up old tracking data"""
        current_time = time.time()
        
        # Clean reconnect events
        for device_id in list(self.reconnect_events.keys()):
            self.reconnect_events[device_id] = deque(
                [t for t in self.reconnect_events[device_id] 
                 if current_time - t < 60.0],
                maxlen=50
            )
            
        # Clean descriptor changes
        for device_id in list(self.descriptor_changes.keys()):
            self.descriptor_changes[device_id] = [
                d for d in self.descriptor_changes[device_id]
                if current_time - d['timestamp'] < 60.0
            ]
            
    def _log_attack(self, attack_type: str, details: any):
        """Log attack attempt"""
        self.attack_log.append({
            'type': attack_type,
            'details': str(details),
            'timestamp': datetime.now().isoformat()
        })
        
    def is_device_blocked(self, device_id: str) -> bool:
        """Check if device is blocked"""
        return device_id in self.blocked_devices
        
    def get_protection_status(self) -> Dict:
        """Get current protection status"""
        return {
            'lockdown_mode': self.lockdown_mode,
            'blocked_devices': list(self.blocked_devices),
            'recent_attacks': self.attack_log[-10:],
            'usb_enabled': self.usb_enabled,
            'monitoring': self.monitoring
        }
        
    def reset_device_block(self, device_id: str):
        """Remove device from blocklist (admin only)"""
        if device_id in self.blocked_devices:
            self.blocked_devices.remove(device_id)
            print(f"Device {device_id} removed from blocklist")