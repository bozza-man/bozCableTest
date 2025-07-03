#!/usr/bin/env python3
"""
Comprehensive USB Threat Signature Database
Contains known malicious USB device signatures and patterns
"""

from typing import Dict, List, Tuple, Set

class ThreatDatabase:
    """Database of known USB threats and malicious device signatures"""
    
    def __init__(self):
        # Known malicious VID/PID combinations
        self.malicious_vid_pid: List[Tuple[str, str, str]] = [
            # Format: (VID, PID, Description)
            # Arduino-based BadUSB (confirmed malicious use)
            ('0x2341', '0x8037', 'Arduino Leonardo/Micro - common BadUSB platform'),
            ('0x2341', '0x8036', 'Arduino Leonardo clone - BadUSB'),
            ('0x1b4f', '0x9206', 'Arduino Leonardo - can be malicious'),
            ('0x1b4f', '0x9207', 'Arduino Micro - can be malicious'),
            ('0x2a03', '0x8037', 'Arduino Leonardo official - can be malicious'),
            
            # Teensy devices (powerful HID attack platform)
            ('0x16c0', '0x0478', 'Teensy 2.0 - HID attack device'),
            ('0x16c0', '0x0483', 'TeensyDuino HID'),
            ('0x16c0', '0x0486', 'Teensy Keyboard/Mouse/Joystick'),
            ('0x16c0', '0x0487', 'Teensy Serial/Keyboard/Mouse/Joystick'),
            ('0x16c0', '0x048a', 'Teensy Keyboard'),
            ('0x16c0', '0x27db', 'Teensy HID device'),
            
            # DigiSpark/ATtiny85 devices
            ('0x16d0', '0x0753', 'Digispark - ATtiny85 BadUSB'),
            ('0x1781', '0x0c9f', 'ATtiny85 USB bootloader'),
            ('0x16c0', '0x05df', 'HID Bootloader - ATtiny'),
            
            # Rubber Ducky and clones
            ('0x03eb', '0x2ff4', 'Known BadUSB/Rubber Ducky signature'),
            ('0x05ac', '0x024f', 'Fake Apple device - Ducky clone'),
            ('0xfeed', '0xdeed', 'USB Rubber Ducky signature'),
            
            # WiFi-enabled BadUSB
            ('0x1d50', '0x60a7', 'WiFi Duck/BadUSB'),
            ('0x1d50', '0x60a8', 'WiFi Duck variant'),
            ('0x239a', '0x8028', 'Cactus WHID - WiFi HID injector'),
            
            # Fake/spoofed legitimate devices
            ('0x05ac', '0x2227', 'Fake Apple keyboard'),
            ('0x05ac', '0x0250', 'Spoofed Apple Aluminium Keyboard'),
            ('0x05ac', '0x1227', 'Fake Apple Mobile Device'),
            ('0x046d', '0xc534', 'Fake Logitech Unifying receiver'),
            ('0x046d', '0xc31c', 'Fake Logitech keyboard'),
            ('0x413c', '0x2003', 'Fake Dell keyboard'),
            ('0x045e', '0x0750', 'Fake Microsoft keyboard'),
            
            # Serial converters (used in keyloggers/BadUSB)
            ('0x0403', '0x6001', 'FTDI - used in keyloggers'),
            ('0x10c4', '0xea60', 'CP2102 - used in BadUSB'),
            ('0x067b', '0x2303', 'Prolific - used in malicious cables'),
            ('0x1a86', '0x7523', 'CH340 - common in malicious devices'),
            ('0x0483', '0x5740', 'STM32 Virtual COM - BadUSB capable'),
            
            # ESP-based attack devices
            ('0x10c4', '0xea60', 'ESP8266/ESP32 Serial - WiFi BadUSB'),
            ('0x1a86', '0x55d4', 'ESP32-S2 - BadUSB capable'),
            
            # Known malicious/suspicious
            ('0xf000', '0x0001', 'Generic HID injection device'),
            ('0x1337', '0x1337', 'L33t h4x0r device'),
            ('0xdead', '0xbeef', 'Malicious test device'),
            ('0x0000', '0x0000', 'Invalid VID/PID - suspicious'),
            ('0xffff', '0xffff', 'Invalid VID/PID - suspicious'),
            
            # Raspberry Pi Zero (when used as BadUSB)
            ('0x1d6b', '0x0104', 'Raspberry Pi Zero - USB Gadget mode'),
            ('0x1d50', '0x6089', 'Raspberry Pi Zero W - BadUSB mode'),
            
            # Other HID attack platforms
            ('0xfeed', '0x1307', 'Plaid Pad - potential HID injection'),
            ('0x16c0', '0x05e1', 'USBaspLoader - DIY HID device'),
            ('0x2e8a', '0x000a', 'Raspberry Pi Pico - can be BadUSB'),
            ('0x239a', '0x8028', 'Adafruit Circuit Playground - HID capable'),
        ]
        
        # HAK5 and other commercial pentesting tools
        self.hak5_signatures = {
            'omg_cable': [
                'O.MG Cable',
                'O.MG-Cable',
                'OMG Cable',
                'DemonSeed',
                'WiFi Duck'
            ],
            'rubber_ducky': [
                'USB Rubber Ducky',
                'Bad USB',
                'BadUSB',
                'Ducky',
                'HAK5'
            ],
            'bash_bunny': [
                'Bash Bunny',
                'BashBunny',
                'Bunny',
                'HAK5 Bunny'
            ],
            'lan_turtle': [
                'LAN Turtle',
                'LANTurtle',
                'Turtle'
            ],
            'key_croc': [
                'Key Croc',
                'KeyCroc',
                'Croc'
            ],
            'packet_squirrel': [
                'Packet Squirrel',
                'PacketSquirrel',
                'Squirrel'
            ],
            'shark_jack': [
                'Shark Jack',
                'SharkJack',
                'Shark'
            ]
        }
        
        # USB device class combinations that are suspicious
        self.suspicious_class_combinations = [
            # Single device presenting multiple classes
            {'HID', 'Mass Storage'},  # Keyboard + Storage
            {'HID', 'Network'},        # Keyboard + Network
            {'Mass Storage', 'Network'},  # Storage + Network
            {'HID', 'Audio'},          # Keyboard + Audio (keylogger)
            {'HID', 'Video'},          # Keyboard + Video (screen capture)
            {'HID', 'Serial'},         # Keyboard + Serial (backdoor)
        ]
        
        # Suspicious device strings and descriptors
        self.suspicious_strings = [
            # HID injection keywords
            'keyboard',
            'keylogger',
            'keystroke',
            'injection',
            'hid',
            'human interface',
            'input device',
            
            # Network backdoor keywords
            'ethernet',
            'network adapter',
            'rndis',
            'ecm',
            'ncm',
            'lan',
            'wifi',
            '802.11',
            
            # Mass storage keywords (for exfiltration)
            'mass storage',
            'removable',
            'flash',
            'thumb',
            
            # Known malicious tools
            'metasploit',
            'empire',
            'cobalt',
            'mimikatz',
            'responder',
            'evil',
            'malicious',
            'exploit',
            'payload',
            'backdoor',
            'trojan',
            'rootkit',
            
            # Suspicious generic names
            'device',
            'gadget',
            'unknown',
            'composite',
            'multifunction',
            
            # DIY/Maker keywords
            'arduino',
            'teensy',
            'digispark',
            'attiny',
            'atmega',
            'raspberry',
            'esp8266',
            'esp32',
            'nodemcu',
            'stm32',
            'bluepill',
            'blackpill'
        ]
        
        # Behavioral patterns that indicate malicious activity
        self.behavioral_patterns = {
            'rapid_enumeration': {
                'threshold': 5,  # More than 5 enumerations per second
                'description': 'Device enumerating too quickly (common in brute-force attacks)'
            },
            'descriptor_morphing': {
                'threshold': 3,  # More than 3 descriptor changes
                'description': 'Device changing descriptors (BadUSB behavior)'
            },
            'rapid_reconnect': {
                'threshold': 10,  # More than 10 reconnects in 30 seconds
                'description': 'Device reconnecting rapidly (DigiSpark behavior)'
            },
            'delayed_enumeration': {
                'threshold': 5000,  # Takes more than 5 seconds to enumerate
                'description': 'Device with suspicious enumeration delay'
            },
            'multiple_interfaces': {
                'threshold': 4,  # More than 4 interfaces
                'description': 'Device with excessive interfaces'
            },
            'single_interface_keyboard': {
                'threshold': 1,  # Only 1 interface for keyboard (suspicious)
                'description': 'Keyboard with single interface (legitimate keyboards have 2+)'
            },
            'high_power_draw': {
                'threshold': 500,  # More than 500mA for non-charging cable
                'description': 'Excessive power consumption (possible WiFi/radio)'
            },
            'vid_pid_change': {
                'threshold': 1,  # Any VID/PID change
                'description': 'Device changing USB identifiers (spoofing attack)'
            },
            'bootloader_mode': {
                'threshold': 1,  # Unexpected bootloader mode
                'description': 'Device entering bootloader/DFU mode unexpectedly'
            }
        }
        
        # Known attack patterns
        self.attack_patterns = {
            'keystroke_injection': [
                'rapid HID reports',
                'automated typing patterns',
                'command sequence detection',
                'shell command patterns'
            ],
            'network_backdoor': [
                'DHCP server on device',
                'unexpected IP assignment',
                'reverse shell connections',
                'DNS hijacking attempts'
            ],
            'data_exfiltration': [
                'rapid file access patterns',
                'systematic directory traversal',
                'large data transfers',
                'hidden partition access'
            ],
            'firmware_attack': [
                'DFU mode unexpected',
                'bootloader access',
                'firmware update requests',
                'low-level device access'
            ]
        }
        
        # Legitimate cables that should be whitelisted
        self.legitimate_cables = [
            # Apple cables
            ('0x05ac', '0x12a8', 'Genuine Apple Lightning Cable'),
            ('0x05ac', '0x1463', 'Genuine Apple USB-C Cable'),
            ('0x05ac', '0x1462', 'Apple Thunderbolt 3 Cable'),
            
            # Major manufacturers
            ('0x04b8', '0x0202', 'Genuine Epson Cable'),
            ('0x0bda', '0x8153', 'Realtek USB Ethernet'),
            ('0x0b95', '0x1790', 'ASIX USB Ethernet'),
            
            # Thunderbolt certified
            ('0x8087', '0x0b40', 'Intel Thunderbolt 4'),
            ('0x8087', '0x15ea', 'Intel Thunderbolt 3'),
        ]
        
    def check_vid_pid(self, vid: str, pid: str) -> Tuple[bool, str]:
        """Check if VID/PID combination is known malicious"""
        vid = vid.lower()
        pid = pid.lower()
        
        # Check whitelist first
        for legit_vid, legit_pid, desc in self.legitimate_cables:
            if vid == legit_vid.lower() and pid == legit_pid.lower():
                return False, f"Legitimate device: {desc}"
        
        # Check blacklist
        for mal_vid, mal_pid, desc in self.malicious_vid_pid:
            if vid == mal_vid.lower() and pid == mal_pid.lower():
                return True, f"Known malicious device: {desc}"
                
        return False, "Unknown device"
        
    def check_device_name(self, name: str) -> Tuple[bool, List[str]]:
        """Check device name for suspicious strings"""
        name_lower = name.lower()
        threats = []
        
        # Check HAK5 signatures
        for tool_type, signatures in self.hak5_signatures.items():
            for sig in signatures:
                if sig.lower() in name_lower:
                    threats.append(f"HAK5 {tool_type} detected: {sig}")
                    
        # Check suspicious strings
        for sus_string in self.suspicious_strings:
            if sus_string.lower() in name_lower:
                threats.append(f"Suspicious keyword in name: {sus_string}")
                
        return len(threats) > 0, threats
        
    def check_device_classes(self, classes: Set[str]) -> Tuple[bool, str]:
        """Check for suspicious combinations of USB device classes"""
        for suspicious_combo in self.suspicious_class_combinations:
            if suspicious_combo.issubset(classes):
                combo_str = ' + '.join(suspicious_combo)
                return True, f"Suspicious class combination: {combo_str}"
                
        return False, "Normal class combination"
        
    def get_behavioral_threshold(self, pattern: str) -> Dict:
        """Get threshold for behavioral pattern"""
        return self.behavioral_patterns.get(pattern, {})
        
    def check_manufacturer(self, manufacturer: str) -> Tuple[bool, str]:
        """Check manufacturer string for suspicious patterns"""
        if not manufacturer:
            return True, "No manufacturer information (suspicious)"
            
        manufacturer_lower = manufacturer.lower()
        
        suspicious_manufacturers = [
            'unknown',
            'generic',
            'noname',
            'test',
            'debug',
            'development',
            'prototype',
            'diy',
            'custom',
            'modified'
        ]
        
        for sus_mfg in suspicious_manufacturers:
            if sus_mfg in manufacturer_lower:
                return True, f"Suspicious manufacturer: {manufacturer}"
                
        return False, "Manufacturer appears legitimate"
        
    def get_attack_indicators(self, attack_type: str) -> List[str]:
        """Get indicators for specific attack type"""
        return self.attack_patterns.get(attack_type, [])