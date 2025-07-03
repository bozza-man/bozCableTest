# Cable Tester Production Scripts

## Main Scripts

### launch_cable_tester.sh
The primary launch script that starts the cable tester with dynamic UI in tmux sessions.
- Starts backend server and frontend UI
- Handles port conflicts automatically
- Opens in Warp terminal with proper window management

Usage: `./launch_cable_tester.sh`

### cable_tester_manager.py
Central management tool for controlling the cable tester system.
- Start/stop backend and frontend services
- View logs and system status
- Clean up old log files
- Run in tmux sessions

Usage:
```bash
python cable_tester_manager.py start backend
python cable_tester_manager.py start frontend
python cable_tester_manager.py status
python cable_tester_manager.py logs backend
python cable_tester_manager.py stop backend
```

### cleanup.sh
Cleanup script for terminating backend processes and freeing ports.
- Kills processes using port 8765
- Terminates any running backend servers
- Optionally kills tmux sessions

Usage: 
```bash
./cleanup.sh                    # Clean backend only
./cleanup.sh --kill-sessions    # Also kill tmux sessions
```

### setup.sh
Initial setup script for the cable tester environment.
- Installs Python dependencies
- Makes scripts executable
- Displays setup instructions

Usage: `./setup.sh`

## Python Modules

### Core Components
- `src/backend_server.py` - WebSocket backend server with logging
- `src/frontend_dynamic.py` - Enhanced dynamic terminal UI with SSH management
- `src/frontend_simple.py` - Simple console frontend
- `src/frontend_console.py` - Alternative console interface

### Security & Monitoring
- `src/security_monitor.py` - Security threat detection
- `src/bruteforce_protection.py` - Brute force attack protection
- `src/usb_monitor.py` - USB device monitoring
- `src/usb_packet_inspector.py` - USB packet analysis

### Utilities
- `src/ssh_manager.py` - SSH connection management
- `src/ssh_server_manager.py` - SSH server configuration
- `src/logger_config.py` - Centralized logging configuration
- `src/remote_agent.py` - Remote system agent
- `src/cable_tester.py` - Core cable testing logic