#!/usr/bin/env python3

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

class CableTesterLogger:
    def __init__(self, name, log_dir="logs", debug=False):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
            
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler for all logs (rotating)
        all_log_file = self.log_dir / f"{name}_all.log"
        file_handler = logging.handlers.RotatingFileHandler(
            all_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # File handler for errors only
        error_log_file = self.log_dir / f"{name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Security events log
        if name in ['backend', 'security_monitor']:
            security_log_file = self.log_dir / "security_events.log"
            security_handler = logging.handlers.RotatingFileHandler(
                security_log_file,
                maxBytes=10*1024*1024,
                backupCount=10
            )
            security_handler.setLevel(logging.WARNING)
            security_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(security_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO if not debug else logging.DEBUG)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
    def get_logger(self):
        return self.logger
        
    @staticmethod
    def setup_global_logging(debug=False):
        """Setup logging for the entire application"""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create session log
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_log = log_dir / f"session_{session_id}.log"
        
        # Add session file handler
        session_handler = logging.FileHandler(session_log)
        session_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(session_handler)
        
        return session_log
        
    @staticmethod
    def get_recent_logs(log_name="all", lines=100):
        """Get recent log entries"""
        log_dir = Path("logs")
        log_files = {
            'all': '*_all.log',
            'errors': '*_errors.log',
            'security': 'security_events.log',
            'backend': 'backend_all.log',
            'frontend': 'frontend_all.log'
        }
        
        pattern = log_files.get(log_name, '*_all.log')
        files = list(log_dir.glob(pattern))
        
        if not files:
            return []
            
        # Get most recent file
        latest_file = max(files, key=os.path.getctime)
        
        # Read last N lines
        with open(latest_file, 'r') as f:
            lines_list = f.readlines()
            return lines_list[-lines:]
            
    @staticmethod
    def clear_old_logs(days=7):
        """Clear logs older than specified days"""
        import time
        log_dir = Path("logs")
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        for log_file in log_dir.glob("*.log*"):
            if os.path.getctime(log_file) < cutoff_time:
                log_file.unlink()
                print(f"Deleted old log: {log_file}")