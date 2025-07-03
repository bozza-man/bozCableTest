# Warp Terminal Integration

The Cable Tester now includes seamless integration with Warp terminal, providing multiple layout options for monitoring and control.

## Quick Start

```bash
./launch.sh
```

This will present a menu with different layout options.

## Available Layouts

### 1. Split View
```
┌─────────────────┬─────────────────┐
│                 │                 │
│    Backend      │    Frontend     │
│    Server       │    Console      │
│                 │                 │
├─────────────────┴─────────────────┤
│          Live Logs                 │
│                                    │
└────────────────────────────────────┘
```

Launch with: `python3 warp_launcher.py split`

### 2. Tabs View
- Tab 1: Backend Server
- Tab 2: Frontend Console  
- Tab 3: Live Logs

Launch with: `python3 warp_launcher.py tabs`

### 3. Monitor View (4-Pane Dashboard)
```
┌─────────────────┬─────────────────┐
│    Backend      │    Frontend     │
│    Server       │    Console      │
├─────────────────┼─────────────────┤
│    Monitor      │    All Logs     │
│   Dashboard     │     Stream      │
└─────────────────┴─────────────────┘
```

Launch with: `python3 warp_launcher.py monitor`

### 4. Simple Split (Original)
Basic horizontal split with backend and frontend side-by-side.

Launch with: `./launch_in_warp.sh`

## Features

### Custom Tmux Configuration
- Mouse support enabled
- Custom color scheme (blue/red theme)
- Pane titles showing component names
- Vi-style key bindings
- Enhanced status bar

### Monitoring Dashboard
The monitor view includes a real-time dashboard showing:
- Backend/Frontend status (✅ Running / ❌ Stopped)
- Recent log entries
- Security events
- Auto-refreshes every 2 seconds

### Automatic Setup
- Creates new Warp window
- Sets up tmux session with chosen layout
- Activates virtual environment
- Starts backend server
- Waits 3 seconds then starts frontend
- Begins log monitoring

## Tmux Controls

| Action | Key Combination |
|--------|----------------|
| Switch panes | `Ctrl+B` then arrow keys |
| Switch panes (alt) | `Ctrl+B` then `o` |
| Switch windows/tabs | `Ctrl+B` then `n`/`p` |
| Resize pane | `Ctrl+B` then `Ctrl+Arrow` |
| Detach session | `Ctrl+B` then `d` |
| Kill pane | `Ctrl+B` then `x` |
| Kill session | `Ctrl+B` then `:kill-session` |

## Session Management

### List Active Sessions
```bash
tmux ls
```

### Reattach to Session
```bash
tmux attach -t cable_tester
# or
tmux attach -t cable_monitor
```

### Kill All Cable Tester Sessions
```bash
python3 warp_launcher.py kill
```

## Requirements

1. **Warp Terminal**: Download from https://www.warp.dev
2. **tmux**: Installed via homebrew
3. **Python venv**: Must be set up in project directory

## Troubleshooting

### Warp Not Found
```
Error: Warp terminal is not installed
```
Install Warp from https://www.warp.dev

### Virtual Environment Missing
```
Error: Virtual environment not found
```
Run:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Sessions Already Exist
Kill existing sessions:
```bash
python3 warp_launcher.py kill
```

### Permission Denied
Make scripts executable:
```bash
chmod +x launch.sh launch_in_warp.sh warp_launcher.py
```

## Advanced Usage

### Custom Tmux Config
The launcher creates `.cable_tester_tmux.conf` with optimized settings. You can modify this file to customize the tmux environment.

### Debug Mode
To launch with debug logging:
1. Use monitor view for real-time log streaming
2. Or modify the launch commands to include `--debug` flag

### Remote Monitoring
You can detach from the session (`Ctrl+B d`) and reattach later while the tests continue running in the background.

## Integration with Cable Tester Manager

The Warp launcher works seamlessly with the cable tester manager:

```bash
# Start in background (no UI)
python3 cable_tester_manager.py start backend --debug

# Then attach with Warp for monitoring
python3 warp_launcher.py monitor
```

This allows you to have persistent backend services while connecting/disconnecting the UI as needed.