#!/bin/bash

echo "Setting up USB-C/Thunderbolt Cable Tester..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3."
    exit 1
fi

# Install required packages
echo "Installing required Python packages..."
pip3 install -r requirements.txt

# Make scripts executable
chmod +x src/*.py

echo "Setup complete!"
echo ""
echo "To run the cable tester:"
echo "  python3 src/cable_tester.py"
echo ""
echo "Important: This tool requires:"
echo "  1. Two Macs connected via the cable to be tested"
echo "  2. SSH access to the remote Mac"
echo "  3. Admin privileges may be required for some tests"