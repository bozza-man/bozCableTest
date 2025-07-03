#!/usr/bin/env python3

import subprocess
import sys
import time
import os
import signal
from pathlib import Path
import argparse

class CableTesterManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.venv_python = self.base_dir / "venv" / "bin" / "python"
        self.log_dir = self.base_dir / "logs"
        self.pid_dir = self.base_dir / "pids"
        self.pid_dir.mkdir(exist_ok=True)
        
    def start_backend(self, debug=False):
        """Start backend server"""
        print("Starting backend server...")
        
        backend_script = self.base_dir / "src" / "backend_server_logged.py"
        pid_file = self.pid_dir / "backend.pid"
        
        # Check if already running
        if pid_file.exists():
            pid = int(pid_file.read_text())
            if self._is_process_running(pid):
                print(f"Backend already running (PID: {pid})")
                return
                
        # Start backend
        cmd = [str(self.venv_python), str(backend_script)]
        if debug:
            cmd.append("--debug")
            
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        
        # Save PID
        pid_file.write_text(str(process.pid))
        
        # Wait for startup
        time.sleep(2)
        
        if process.poll() is None:
            print(f"Backend started successfully (PID: {process.pid})")
            print(f"Logs: {self.log_dir}/backend_all.log")
        else:
            print("Backend failed to start")
            
    def start_frontend(self):
        """Start frontend console"""
        print("Starting frontend console...")
        
        frontend_script = self.base_dir / "src" / "frontend_simple_fixed.py"
        
        # Run frontend interactively
        subprocess.run([str(self.venv_python), str(frontend_script)])
        
    def stop_backend(self):
        """Stop backend server gracefully"""
        pid_file = self.pid_dir / "backend.pid"
        
        if not pid_file.exists():
            print("Backend not running")
            return
            
        pid = int(pid_file.read_text())
        
        if not self._is_process_running(pid):
            print("Backend not running")
            pid_file.unlink()
            return
            
        print(f"Stopping backend (PID: {pid})...")
        
        # Send SIGTERM for graceful shutdown
        try:
            os.kill(pid, signal.SIGTERM)
            
            # Wait for process to end
            for _ in range(10):
                if not self._is_process_running(pid):
                    break
                time.sleep(0.5)
            else:
                # Force kill if not stopped
                os.kill(pid, signal.SIGKILL)
                
            pid_file.unlink()
            print("Backend stopped")
            
        except ProcessLookupError:
            pid_file.unlink()
            print("Backend already stopped")
            
    def status(self):
        """Show system status"""
        print("\n=== Cable Tester Status ===\n")
        
        # Backend status
        pid_file = self.pid_dir / "backend.pid"
        if pid_file.exists():
            pid = int(pid_file.read_text())
            if self._is_process_running(pid):
                print(f"Backend: RUNNING (PID: {pid})")
                
                # Check WebSocket port
                result = subprocess.run(
                    ["lsof", "-ti:8765"],
                    capture_output=True,
                    text=True
                )
                if result.stdout.strip():
                    print("WebSocket: LISTENING on port 8765")
            else:
                print("Backend: STOPPED (stale PID file)")
                pid_file.unlink()
        else:
            print("Backend: STOPPED")
            
        # Log status
        print(f"\nLog directory: {self.log_dir}")
        if self.log_dir.exists():
            log_files = list(self.log_dir.glob("*.log"))
            print(f"Log files: {len(log_files)}")
            
            # Show recent logs
            latest_logs = sorted(log_files, key=os.path.getmtime, reverse=True)[:3]
            if latest_logs:
                print("\nRecent log files:")
                for log in latest_logs:
                    size = log.stat().st_size / 1024  # KB
                    print(f"  - {log.name} ({size:.1f} KB)")
                    
    def view_logs(self, log_type="backend", lines=50, follow=False):
        """View log files"""
        log_files = {
            'backend': self.log_dir / "backend_all.log",
            'frontend': self.log_dir / "frontend_all.log",
            'security': self.log_dir / "security_events.log",
            'errors': self.log_dir / "backend_errors.log"
        }
        
        log_file = log_files.get(log_type)
        if not log_file or not log_file.exists():
            print(f"Log file not found: {log_type}")
            return
            
        if follow:
            # Follow log in real-time
            print(f"Following {log_file.name} (Ctrl+C to stop)...")
            subprocess.run(["tail", "-f", str(log_file)])
        else:
            # Show last N lines
            print(f"\n=== Last {lines} lines of {log_file.name} ===\n")
            subprocess.run(["tail", f"-{lines}", str(log_file)])
            
    def clean_logs(self, days=7):
        """Clean old log files"""
        from logger_config import CableTesterLogger
        
        print(f"Cleaning logs older than {days} days...")
        CableTesterLogger.clear_old_logs(days)
        
    def run_tmux_session(self):
        """Run backend and frontend in tmux"""
        print("Starting tmux sessions...")
        
        # Kill existing sessions
        subprocess.run(["tmux", "kill-session", "-t", "cable_backend"], 
                      stderr=subprocess.DEVNULL)
        subprocess.run(["tmux", "kill-session", "-t", "cable_frontend"], 
                      stderr=subprocess.DEVNULL)
        
        # Create backend session
        subprocess.run([
            "tmux", "new-session", "-d", "-s", "cable_backend",
            f"cd {self.base_dir} && source venv/bin/activate && "
            f"python src/backend_server_logged.py"
        ])
        
        time.sleep(2)
        
        # Create frontend session
        subprocess.run([
            "tmux", "new-session", "-d", "-s", "cable_frontend",
            f"cd {self.base_dir} && source venv/bin/activate && "
            f"python src/frontend_simple_fixed.py"
        ])
        
        print("\nTmux sessions started:")
        print("  - Backend:  tmux attach -t cable_backend")
        print("  - Frontend: tmux attach -t cable_frontend")
        print("\nUse 'tmux kill-session -t <name>' to stop")
        
    def _is_process_running(self, pid):
        """Check if process is running"""
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False

def main():
    parser = argparse.ArgumentParser(description='Cable Tester Manager')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start services')
    start_parser.add_argument('service', choices=['backend', 'frontend', 'all'])
    start_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop services')
    stop_parser.add_argument('service', choices=['backend', 'all'])
    
    # Status command
    subparsers.add_parser('status', help='Show system status')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='View logs')
    logs_parser.add_argument('type', choices=['backend', 'frontend', 'security', 'errors'])
    logs_parser.add_argument('-n', '--lines', type=int, default=50, help='Number of lines')
    logs_parser.add_argument('-f', '--follow', action='store_true', help='Follow log')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean old logs')
    clean_parser.add_argument('--days', type=int, default=7, help='Days to keep')
    
    # Tmux command
    subparsers.add_parser('tmux', help='Run in tmux sessions')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    manager = CableTesterManager()
    
    if args.command == 'start':
        if args.service == 'backend':
            manager.start_backend(debug=args.debug)
        elif args.service == 'frontend':
            manager.start_frontend()
        elif args.service == 'all':
            manager.start_backend(debug=args.debug)
            time.sleep(2)
            manager.start_frontend()
            
    elif args.command == 'stop':
        if args.service in ['backend', 'all']:
            manager.stop_backend()
            
    elif args.command == 'status':
        manager.status()
        
    elif args.command == 'logs':
        manager.view_logs(args.type, args.lines, args.follow)
        
    elif args.command == 'clean':
        manager.clean_logs(args.days)
        
    elif args.command == 'tmux':
        manager.run_tmux_session()

if __name__ == '__main__':
    main()