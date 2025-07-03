#!/usr/bin/env python3

import time
import json
from datetime import datetime

def run_demo():
    """Run a demonstration of the cable tester functionality"""
    print("\n=== USB-C/Thunderbolt Cable Tester - DEMO MODE ===")
    print("\nThis demo shows how the cable tester works without actual hardware.\n")
    
    print("In a real test, you would:")
    print("1. Connect to a remote Mac via SSH")
    print("2. Insert the cable between the two Macs")
    print("3. The tool performs security scanning first")
    print("4. If safe, performance tests are run\n")
    
    input("Press Enter to see a simulated test run...")
    
    # Simulate security test
    print("\n=== SECURITY TEST ===")
    print("Capturing baseline USB state...")
    time.sleep(1)
    print("Please connect the cable between the two Macs now.")
    print("Monitoring for cable insertion...")
    time.sleep(2)
    
    print("\nNew device detected: USB-C Cable")
    print("VID: 0x05ac, PID: 0x1234")
    print("Analyzing cable for security threats...")
    time.sleep(2)
    
    print("✅ Cable passed security checks")
    print("Cable authorized with hash: a3f5c2b8e9d1f4a6...")
    
    # Ask to continue
    response = input("\nCable is safe. Run performance tests? (y/n): ")
    if response.lower() != 'y':
        return
    
    # Simulate performance tests
    print("\n=== PERFORMANCE TESTS ===")
    
    # Data transfer test
    print("\n--- Data Transfer Test ---")
    for size in [1, 10, 100]:
        print(f"Testing {size}MB file transfer...")
        time.sleep(1)
        speed = 5000 / (size / 10)  # Simulate varying speeds
        print(f"  Transfer speed: {speed:.2f} Mbps")
    
    print("\nDetected cable generation: USB 3.2 Gen 2")
    
    # Power delivery test
    print("\n--- Power Delivery Test ---")
    time.sleep(1)
    print("Power delivery detected:")
    print("  Current: 3000 mA")
    print("  Power State: Active")
    
    # Thunderbolt test
    print("\n--- Thunderbolt Test ---")
    time.sleep(1)
    print("No Thunderbolt connection detected")
    
    # Signal integrity test
    print("\n--- Signal Integrity Test ---")
    print("Running signal integrity test (simulated 5 seconds)...")
    time.sleep(5)
    print("Completed 47 transfers")
    print("Error rate: 0.00%")
    
    # Generate report
    print("\n\n=== CABLE TEST REPORT ===")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nSecurity Test: PASSED")
    print("  Cable Hash: a3f5c2b8e9d1f4a6...")
    print("\nData Transfer Test: COMPLETED")
    print("  Average Speed: 3426.67 Mbps")
    print("  Detected Generation: USB 3.2 Gen 2")
    print("\nPower Delivery Test: COMPLETED")
    print("  Current: 3000 mA")
    print("\nThunderbolt Test: NOT_DETECTED")
    print("\nSignal Integrity Test: COMPLETED")
    print("  Error Rate: 0.00%")
    
    print("\nDemo complete! In a real test, detailed results would be saved to a JSON file.")

def show_malicious_cable_demo():
    """Show what happens when a malicious cable is detected"""
    print("\n=== MALICIOUS CABLE DETECTION DEMO ===")
    print("\nThis demo shows what happens when a malicious cable is detected.\n")
    
    input("Press Enter to simulate connecting a malicious cable...")
    
    print("\n=== SECURITY TEST ===")
    print("Capturing baseline USB state...")
    time.sleep(1)
    print("Please connect the cable between the two Macs now.")
    print("Monitoring for cable insertion...")
    time.sleep(2)
    
    print("\nNew device detected: USB Composite Device")
    print("VID: 0x03eb, PID: 0x2ff4")
    print("Analyzing cable for security threats...")
    time.sleep(2)
    
    print("\n⚠️  SECURITY ALERT ⚠️")
    print("Suspicious activity detected!")
    print("  - Suspicious VID/PID combination: 0x03eb:0x2ff4")
    print("  - HID functionality in cable device")
    print("  - Multiple device functions detected (potential BadUSB)")
    
    print("\n❌ CABLE FAILED SECURITY CHECKS")
    print("Threats detected:")
    print("  - Potential rubber_ducky detected: Bad USB")
    print("  - Suspicious VID/PID combination")
    print("  - Multiple device functions detected")
    
    print("\n⚠️  DO NOT USE THIS CABLE ⚠️")
    print("The cable may contain malicious hardware.")
    print("\nPerformance tests will not be run on unauthorized cables.")

if __name__ == "__main__":
    print("Cable Tester Demo Options:")
    print("1. Normal cable test (safe cable)")
    print("2. Malicious cable detection")
    
    choice = input("\nSelect demo (1 or 2): ")
    
    if choice == "1":
        run_demo()
    elif choice == "2":
        show_malicious_cable_demo()
    else:
        print("Invalid choice")