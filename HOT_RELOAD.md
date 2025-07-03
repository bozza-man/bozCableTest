# Hot Reload Development Guide

The Cable Tester now supports **in-place code updates** without losing WebSocket connections or application state!

## Quick Start

```bash
# Launch development mode with auto-reload
./launch_dev_mode.sh

# Or launch basic reloadable servers
./start_reloadable.sh
```

## Features

- 🔄 **Hot Code Reload**: Update Python code without restarting servers
- 🔌 **Connection Preservation**: WebSocket connections stay alive during reload
- 📝 **File Watching**: Automatic reload when source files change
- 🚀 **Zero Downtime**: No interruption to running operations
- 🛡️ **Safe Reload**: Graceful handling of syntax errors

## Architecture

### Reloadable Backend (`backend_with_reload.py`)
- Wraps the original backend in a reloadable container
- Preserves WebSocket connections during module reload
- Safely stops and restarts USB/security monitoring
- Handles reload commands via WebSocket

### Reloadable Frontend (`frontend_with_reload.py`)
- Wraps the original frontend with reload capability
- Maintains backend connection during reload
- Provides reload commands in the UI

### File Watcher (`file_watcher.py`)
- Monitors source files for changes
- Automatically triggers backend reload
- Configurable watch directory and extensions
- Built-in cooldown to prevent reload storms

## Usage

### Development Mode (Recommended)

Launch the full development environment:

```bash
./launch_dev_mode.sh
```

This creates a 4-pane tmux session:
- **Top Left**: Reloadable backend server
- **Top Right**: File watcher (auto-reload on save)
- **Bottom Left**: Reloadable frontend
- **Bottom Right**: Live error/warning logs

### Manual Reload

From the frontend, type:
- `reload` - Reload frontend code
- `reload-backend` - Reload backend code

From anywhere:
```bash
./reload.sh  # Reload backend via WebSocket
```

### Programmatic Reload

Send a WebSocket message:
```python
await websocket.send(json.dumps({'type': 'reload_backend'}))
```

## What Gets Reloaded

When you trigger a reload:
1. All Python modules are reloaded with `importlib.reload()`
2. New instances of classes are created
3. WebSocket connections are preserved
4. USB monitoring is stopped and restarted
5. Security monitoring is reset

## Best Practices

1. **Save Often**: With file watching, just save your Python files
2. **Check Logs**: Watch the log pane for reload status
3. **Test Changes**: The frontend stays connected - test immediately
4. **Handle Errors**: Syntax errors won't crash the server

## Limitations

- State in global variables is reset on reload
- Active SSH connections may need reconnection
- Running tests are interrupted by reload

## Troubleshooting

### Reload Fails
- Check for syntax errors in Python files
- Ensure all imports are correct
- Look at the error output in the backend pane

### File Watcher Not Working
- Verify the backend is running on port 8765
- Check that source files are in the `src/` directory
- Ensure file permissions allow reading

### WebSocket Disconnects
- The reloadable wrapper preserves connections
- If disconnected, the frontend will show an error
- Simply reconnect or restart the frontend

## Development Workflow

1. Launch dev mode: `./launch_dev_mode.sh`
2. Make code changes in your editor
3. Save the file - auto-reload triggers
4. Test changes immediately in frontend
5. Check logs for any errors

No more restart cycles - just code and test! 🚀