#!/usr/bin/env python3
"""
Smart logging system that reduces repetitive log entries
and provides better insights into system behavior
"""

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import hashlib
import json

class SmartLogger:
    """Logger that intelligently handles repetitive messages and provides summaries"""
    
    def __init__(self, name: str, base_logger: logging.Logger):
        self.name = name
        self.logger = base_logger
        
        # Track message patterns
        self.message_counts = defaultdict(int)
        self.last_logged = defaultdict(float)
        self.suppressed_counts = defaultdict(int)
        
        # Configuration
        self.suppression_window = 60  # seconds
        self.summary_interval = 300  # 5 minutes
        self.last_summary = time.time()
        
        # Categories of messages to handle differently
        self.polling_patterns = [
            "USB Event: device_",
            "Broadcasting: usb_update",
            "Broadcasting: status_update",
            "Checking USB devices",
            "Monitoring for cable insertion",
            "New network interfaces detected",
            "Device : is blocked",
        ]
        
        # Important messages to always log
        self.always_log_patterns = [
            "ERROR",
            "CRITICAL",
            "SECURITY ALERT",
            "Client connected",
            "Client disconnected",
            "SSH connection",
            "Test started",
            "Test completed",
            "Cable authorized",
            "Threat detected",
            "Starting",
            "Stopping",
            "Shutdown",
        ]
        
        # State tracking
        self.device_state = {}
        self.interface_state = set()
        self.security_events = deque(maxlen=100)
        
    def _get_message_key(self, message: str) -> str:
        """Generate a key for message deduplication"""
        # For some messages, we want to extract the pattern
        for pattern in self.polling_patterns:
            if pattern in message:
                # Extract the base pattern
                if "VID:" in message and "PID:" in message:
                    # For USB device messages, use device ID as key
                    import re
                    vid_match = re.search(r'VID:\s*([0-9a-fA-Fx]+)', message)
                    pid_match = re.search(r'PID:\s*([0-9a-fA-Fx]+)', message)
                    if vid_match and pid_match:
                        return f"{pattern}_{vid_match.group(1)}_{pid_match.group(1)}"
                return pattern
                
        # For other messages, use full message hash
        return hashlib.md5(message.encode()).hexdigest()[:8]
        
    def _should_log_immediately(self, level: str, message: str) -> bool:
        """Check if message should be logged immediately"""
        # Always log errors and above
        if level in ['ERROR', 'CRITICAL']:
            return True
            
        # Check against always-log patterns
        for pattern in self.always_log_patterns:
            if pattern in message:
                return True
                
        return False
        
    def _is_polling_message(self, message: str) -> bool:
        """Check if this is a repetitive polling message"""
        for pattern in self.polling_patterns:
            if pattern in message:
                return True
        return False
        
    def log(self, level: str, message: str, *args, **kwargs):
        """Smart logging with deduplication"""
        # Format message if needed
        if args:
            message = message % args
            
        # Check if we should log immediately
        if self._should_log_immediately(level, message):
            getattr(self.logger, level.lower())(message, **kwargs)
            if "SECURITY" in message:
                self.security_events.append({
                    'timestamp': datetime.now(),
                    'level': level,
                    'message': message
                })
            return
            
        # Get message key for deduplication
        msg_key = self._get_message_key(message)
        current_time = time.time()
        
        # Track message count
        self.message_counts[msg_key] += 1
        
        # Check if this is a polling message
        if self._is_polling_message(message):
            # For polling messages, log less frequently
            last_log_time = self.last_logged.get(msg_key, 0)
            
            # Log polling messages at most once per minute
            if current_time - last_log_time > 60:
                count = self.message_counts[msg_key]
                if count > 1:
                    getattr(self.logger, level.lower())(
                        f"{message} (occurred {count} times in last minute)"
                    )
                else:
                    getattr(self.logger, level.lower())(message)
                    
                self.last_logged[msg_key] = current_time
                self.message_counts[msg_key] = 0
            else:
                self.suppressed_counts[msg_key] += 1
        else:
            # For non-polling messages, use standard deduplication
            last_log_time = self.last_logged.get(msg_key, 0)
            
            if current_time - last_log_time > self.suppression_window:
                # Log the message
                suppressed = self.suppressed_counts.get(msg_key, 0)
                if suppressed > 0:
                    getattr(self.logger, level.lower())(
                        f"{message} (suppressed {suppressed} similar messages)"
                    )
                    self.suppressed_counts[msg_key] = 0
                else:
                    getattr(self.logger, level.lower())(message)
                    
                self.last_logged[msg_key] = current_time
                
        # Check if we should output a summary
        if current_time - self.last_summary > self.summary_interval:
            self._log_summary()
            
    def _log_summary(self):
        """Log a summary of suppressed messages"""
        self.last_summary = time.time()
        
        if not self.suppressed_counts:
            return
            
        self.logger.info("=== Logging Summary ===")
        
        # Group by message type
        polling_suppressed = 0
        other_suppressed = 0
        
        for msg_key, count in self.suppressed_counts.items():
            if count > 0:
                for pattern in self.polling_patterns:
                    if pattern in msg_key:
                        polling_suppressed += count
                        break
                else:
                    other_suppressed += count
                    
        if polling_suppressed > 0:
            self.logger.info(f"Suppressed {polling_suppressed} polling messages")
            
        if other_suppressed > 0:
            self.logger.info(f"Suppressed {other_suppressed} other repetitive messages")
            
        # Log security event summary
        if self.security_events:
            recent_events = [e for e in self.security_events 
                           if (datetime.now() - e['timestamp']).seconds < 300]
            if recent_events:
                self.logger.info(f"Security events in last 5 minutes: {len(recent_events)}")
                
        # Clear suppressed counts
        self.suppressed_counts.clear()
        
    def track_device_change(self, device_id: str, device_info: Dict):
        """Track device state changes"""
        prev_state = self.device_state.get(device_id)
        
        if prev_state != device_info:
            # Only log if there's an actual change
            if prev_state is None:
                self.logger.info(f"New device detected: {device_id} - {device_info.get('name', 'Unknown')}")
            else:
                # Check what changed
                changes = []
                for key in device_info:
                    if device_info.get(key) != prev_state.get(key):
                        changes.append(f"{key}: {prev_state.get(key)} → {device_info.get(key)}")
                        
                if changes:
                    self.logger.warning(f"Device {device_id} changed: {', '.join(changes)}")
                    
            self.device_state[device_id] = device_info.copy()
            
    def track_interfaces(self, interfaces: set):
        """Track network interface changes"""
        new_interfaces = interfaces - self.interface_state
        removed_interfaces = self.interface_state - interfaces
        
        if new_interfaces:
            self.logger.warning(f"New network interfaces: {new_interfaces}")
            
        if removed_interfaces:
            self.logger.info(f"Removed network interfaces: {removed_interfaces}")
            
        self.interface_state = interfaces.copy()
        
    # Convenience methods matching standard logger interface
    def debug(self, message, *args, **kwargs):
        self.log('DEBUG', message, *args, **kwargs)
        
    def info(self, message, *args, **kwargs):
        self.log('INFO', message, *args, **kwargs)
        
    def warning(self, message, *args, **kwargs):
        self.log('WARNING', message, *args, **kwargs)
        
    def error(self, message, *args, **kwargs):
        self.log('ERROR', message, *args, **kwargs)
        
    def critical(self, message, *args, **kwargs):
        self.log('CRITICAL', message, *args, **kwargs)


class SmartLoggerAdapter:
    """Adapter to replace existing loggers with smart loggers"""
    
    def __init__(self, logger: logging.Logger):
        self.smart_logger = SmartLogger(logger.name, logger)
        
    def __getattr__(self, name):
        """Forward all attributes to smart logger"""
        return getattr(self.smart_logger, name)