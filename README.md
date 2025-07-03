# USB-C/Thunderbolt Cable Tester

A comprehensive security-focused cable testing application for macOS that tests USB-C and Thunderbolt cables between two Macs. Features hot-reload development support, advanced threat detection, and tmux-based terminal UI.

## Features

### Security Testing (Priority #1)
- **Malicious Cable Detection**: Detects HAK5 OMG cables, USB Rubber Ducky, BadUSB, and other threats
- **USB Enumeration Monitoring**: Tracks suspicious device behavior and rapid reconnections
- **Device Authorization**: Cables must pass security checks before performance testing
- **Threat Signatures**: Maintains database of known malicious device patterns

### Performance Testing (After Security Clearance)
- **Data Transfer Speed**: Tests USB 2.0 through USB4/Thunderbolt speeds
- **Power Delivery**: Monitors USB-PD capabilities and current draw
- **Thunderbolt Detection**: Verifies Thunderbolt functionality
- **Signal Integrity**: Measures error rates during sustained transfers
- **DisplayPort Alt Mode**: Tests video capabilities (planned)

## Architecture

```
┌─────────────────┐                    ┌─────────────────┐
│   Local Mac     │                    │   Remote Mac    │
│                 │                    │                 │
│ ┌─────────────┐ │     SSH/SFTP      │ ┌─────────────┐ │
│ │Cable Tester │ ├────────────────────┤ │Remote Agent │ │
│ └─────────────┘ │                    │ └─────────────┘ │
│                 │                    │                 │
│ ┌─────────────┐ │                    │ ┌─────────────┐ │
│ │USB Monitor  │ │   USB-C/TB Cable  │ │USB Monitor  │ │
│ └─────────────┘ ├────────────────────┤ └─────────────┘ │
│                 │                    │                 │
└─────────────────┘                    └─────────────────┘
```

## Installation

```bash
# Clone the repository
cd cable_tester

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x src/*.py
```

## Usage

### Quick Start

```bash
# Standard mode with SSH manager
./launch_enhanced.sh

# Development mode with hot reload
./launch_dev_mode.sh

# Menu-driven safe mode
./launch_safe.sh
```

### Running Individual Components

```bash
source venv/bin/activate
python src/cable_tester.py
```

You will be prompted for:
1. Remote Mac IP/hostname
2. SSH username
3. Authentication method (password or SSH key)

### Test Process

1. **Setup Phase**
   - Establishes SSH connection to remote Mac
   - Deploys remote testing agent
   - Captures baseline USB state

2. **Security Test** (Isolated)
   - Connect the cable when prompted
   - Monitors USB enumeration
   - Checks for malicious signatures
   - Cable must pass before continuing

3. **Performance Tests** (If Authorized)
   - Data transfer speed testing
   - Power delivery monitoring
   - Thunderbolt verification
   - Signal integrity testing

4. **Report Generation**
   - Comprehensive JSON report
   - Pass/fail status for each test
   - Detailed metrics and findings

## Security Features

### Threat Detection
- Monitors for HID devices in cables
- Detects suspicious VID/PID combinations
- Tracks rapid reconnection patterns
- Identifies multiple device functions
- Monitors for new network interfaces

### Authorization System
- Generates unique hash for each cable
- Maintains whitelist of authorized cables
- Blocks performance tests on suspicious cables

## Example Output

### Safe Cable
```
=== SECURITY TEST ===
New device detected: USB-C Cable
VID: 0x05ac, PID: 0x1234
✅ Cable passed security checks
Cable authorized with hash: a3f5c2b8e9d1f4a6...

=== PERFORMANCE TESTS ===
Data Transfer Test: USB 3.2 Gen 2 (5000 Mbps)
Power Delivery: 3000 mA
Signal Integrity: 0.00% error rate
```

### Malicious Cable
```
=== SECURITY TEST ===
⚠️  SECURITY ALERT ⚠️
Suspicious activity detected!
- Potential rubber_ducky detected
- HID functionality in cable device
❌ CABLE FAILED SECURITY CHECKS
⚠️  DO NOT USE THIS CABLE ⚠️
```

## Requirements

- macOS (both machines)
- Python 3.8+
- SSH access between Macs
- Admin privileges (for some USB monitoring features)

## Components

- `cable_tester.py`: Main application orchestrator
- `security_monitor.py`: Malicious cable detection
- `ssh_manager.py`: Remote Mac communication
- `usb_monitor.py`: Real-time USB monitoring
- `remote_agent.py`: Runs on remote Mac
- `demo_mode.py`: Demonstration without hardware

## Security Considerations

- Never use untrusted cables without testing
- The tool isolates security testing before any data transfer
- Malicious cables can act as keyboards, network adapters, etc.
- Always verify cable authorization before use

## Hot Reload Development

The project supports in-place code updates without losing connections:

```bash
# Launch development mode
./launch_dev_mode.sh

# Edit any Python file - changes auto-reload
# Or manually reload:
# - Frontend: type 'reload'
# - Backend: type 'reload-backend'
```

See [HOT_RELOAD.md](HOT_RELOAD.md) for detailed documentation.

## Future Enhancements

- GUI interface
- Cable fingerprint database
- Extended Thunderbolt 4 testing
- USB4 specific features
- Automated remediation for threats