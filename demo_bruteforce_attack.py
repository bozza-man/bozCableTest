#!/usr/bin/env python3

import time
from datetime import datetime

print("\n=== USB-C/Thunderbolt Cable Tester - BRUTE-FORCE ATTACK DEMO ===")
print("\nThis demo shows how the system handles brute-force USB attacks.\n")

print("Simulating connection to remote Mac...")
time.sleep(1)
print("Successfully connected to 192.168.1.100")
print("Remote agent started successfully")

print("\n=== SECURITY TEST ===")
print("Capturing baseline USB state...")
print("Starting brute-force protection monitoring...")
print("Starting USB packet inspection...")
time.sleep(1)

print("\nPlease connect the cable between the two Macs now.")
print("Monitoring for cable insertion...")
time.sleep(2)

print("\n⚠️  Detecting unusual USB activity...")

# Simulate rapid enumeration attack
print("\n--- RAPID ENUMERATION ATTACK DETECTED ---")
for i in range(8):
    print(f"New device detected: Unknown Device {i+1}")
    print(f"VID: 0x{1234+i:04x}, PID: 0x{5678+i:04x}")
    time.sleep(0.2)

print("\n⚡ USB enumeration throttled")
print("⚠️  Enumeration rate: 8 devices/second (threshold: 5/sec)")

# Simulate HID flood attack
time.sleep(1)
print("\n--- HID FLOOD ATTACK DETECTED ---")
print("Detecting rapid HID reports...")
print("  HID Keyboard reports: 523 packets/sec")
print("  Pattern: Attempting to inject keystrokes")

print("\n⚠️  USB Pattern Attack Detected: hid_flood")
print("   Count: 523 packets")

# Simulate reconnection attack
time.sleep(1)
print("\n--- RAPID RECONNECTION ATTACK ---")
for i in range(12):
    if i % 2 == 0:
        print(f"Device disconnected")
    else:
        print(f"Device reconnected (attempt {i//2 + 1})")
    time.sleep(0.15)

print("\n⛔ Device blocked: 0x1234:0x5678")
print("Reason: Rapid reconnection attack")
print("⏱️  Adding 5-second delay to port for device 0x1234:0x5678")

# Simulate DMA attempt
time.sleep(1)
print("\n--- THUNDERBOLT DMA ATTEMPT DETECTED ---")
print("Suspicious Thunderbolt configuration detected")
print("  Attempting to access memory regions")
print("  DMA packet pattern detected: 0x87 0x83")

print("\n🚨 CRITICAL: Potential DMA attack detected!")
print("System entering protective mode")

# System enters lockdown
time.sleep(1)
print("\n🚨 USB LOCKDOWN MODE ACTIVATED 🚨")
print("Reason: Potential DMA attack detected")
print("All USB operations suspended")
print("🔒 Disabling non-essential USB...")

print("\n❌ CABLE FAILED SECURITY CHECKS")
print("\nThreats detected:")
print("  - Enumeration flood attack (8 devices/sec)")
print("  - HID injection attack (523 packets)")
print("  - Rapid reconnection attack (6 reconnects)")
print("  - Potential DMA attack attempt")
print("  - Device 0x1234:0x5678 blocked")

print("\n⚠️  DO NOT USE THIS CABLE ⚠️")
print("The cable is attempting multiple attack vectors:")
print("  • Brute-force enumeration to find vulnerabilities")
print("  • HID injection for command execution")
print("  • Rapid reconnection to bypass security")
print("  • DMA access for memory manipulation")

print("\n=== PROTECTION MEASURES ACTIVE ===")
print("✓ USB enumeration throttled")
print("✓ Device 0x1234:0x5678 blocked")
print("✓ HID packets filtered")
print("✓ USB subsystem in lockdown mode")
print("✓ DMA access prevented")

print("\n=== ATTACK LOG ===")
print(f"{datetime.now().strftime('%H:%M:%S')} - Enumeration attack detected")
print(f"{datetime.now().strftime('%H:%M:%S')} - HID Flood Attack: 523 HID packets")
print(f"{datetime.now().strftime('%H:%M:%S')} - Reconnection attack: 0x1234:0x5678")
print(f"{datetime.now().strftime('%H:%M:%S')} - DMA ATTACK ATTEMPT")
print(f"{datetime.now().strftime('%H:%M:%S')} - LOCKDOWN MODE activated")

print("\nSystem will remain in lockdown for 30 seconds...")
print("Security incident logged: security_bruteforce_20241231_144523.json")

# Simulate lockdown timer
for i in range(3):
    time.sleep(1)
    print(f"Lockdown remaining: {30 - (i+1)*10} seconds...")

print("\n✅ Exiting USB lockdown mode")
print("🔓 Re-enabling USB...")
print("\nCable testing aborted due to security threats.")