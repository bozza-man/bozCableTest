#!/usr/bin/env python3

import subprocess
import time
import sys

print("\n=== Testing Frontend/Backend System ===\n")

# Check if websockets is installed
try:
    import websockets
    print("✅ WebSockets module installed")
except ImportError:
    print("❌ WebSockets not installed. Run: pip install websockets")
    sys.exit(1)

print("\nTo run the cable tester with separate frontend/backend:")
print("\n1. Open Terminal 1 and run:")
print("   cd cable_tester")
print("   source venv/bin/activate")
print("   python src/backend_server.py")
print("\n2. Wait for 'Cable Tester Backend starting on ws://localhost:8765'")
print("\n3. Open Terminal 2 and run:")
print("   cd cable_tester")
print("   source venv/bin/activate")
print("   python src/frontend_simple.py")
print("\n4. You should see 'Connected to backend server'")
print("\n5. Use the interactive menu:")
print("   - Press 1 to connect SSH")
print("   - Press 2 to run security test")
print("   - Press 3 to run performance tests")
print("   - Press q to quit")

print("\n" + "="*50)
print("\nFor testing without actual hardware, you can:")
print("1. Use the demo scripts to see how it works")
print("2. Connect two Macs with a USB-C cable")
print("3. Ensure SSH is enabled on the remote Mac")

print("\nThe system will:")
print("- First check cable security (malicious hardware)")
print("- Only run performance tests if cable is safe")
print("- Show real-time updates in the frontend")
print("- Handle brute-force attacks with lockdown mode")