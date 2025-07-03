#!/usr/bin/env python3

import time
from datetime import datetime

print("\n=== USB-C/Thunderbolt Cable Tester - MALICIOUS CABLE DEMO ===")
print("\nThis demo shows what happens when a MALICIOUS cable is detected.\n")

print("Simulating connection to remote Mac...")
time.sleep(1)
print("Successfully connected to 192.168.1.100")
print("Remote agent started successfully")

print("\n=== SECURITY TEST ===")
print("Capturing baseline USB state...")
time.sleep(1)
print("Please connect the cable between the two Macs now.")
print("Monitoring for cable insertion...")
time.sleep(2)

print("\nNew device detected: USB Composite Device")
print("VID: 0x03eb, PID: 0x2ff4")
print("Manufacturer: Unknown")
time.sleep(0.5)

print("\nAdditional device detected: HID Keyboard Device")
print("VID: 0x03eb, PID: 0x2ff5")
time.sleep(0.5)

print("\nNew network interface detected: en7")
print("Interface type: RNDIS/Ethernet Gadget")

print("\nAnalyzing cable for security threats...")
time.sleep(2)

print("\n⚠️  SECURITY ALERT ⚠️")
print("Suspicious activity detected!")
print("  - Multiple device functions detected")
print("  - HID Keyboard functionality in cable")
print("  - Unauthorized network interface created")
print("  - Suspicious VID/PID combination: 0x03eb:0x2ff4")
print("  - Rapid device enumeration pattern detected")

time.sleep(1)

print("\n❌ CABLE FAILED SECURITY CHECKS")
print("\nThreats detected:")
print("  - Potential BadUSB/Rubber Ducky device")
print("  - Unauthorized HID device (can act as keyboard)")
print("  - Network adapter injection (potential data exfiltration)")
print("  - Known malicious VID/PID signature")

print("\n⚠️  DO NOT USE THIS CABLE ⚠️")
print("The cable contains malicious hardware that could:")
print("  • Execute unauthorized commands")
print("  • Steal credentials and data")
print("  • Create backdoor network access")
print("  • Install malware")

print("\nSecurity Test: FAILED")
print("Cable Authorization: DENIED")
print("Performance tests: BLOCKED")

print("\n=== RECOMMENDED ACTIONS ===")
print("1. Disconnect the cable immediately")
print("2. Check system logs for any unauthorized access")
print("3. Run security scan on both systems")
print("4. Report the cable to security team")
print("5. Physically mark/destroy the cable")

print(f"\nSecurity incident logged: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Report saved to: security_alert_cable_20241231_143052.json")