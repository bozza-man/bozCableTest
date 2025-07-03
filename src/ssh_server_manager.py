#!/usr/bin/env python3

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class SSHServerManager:
    def __init__(self):
        self.config_dir = Path.home() / ".cable_tester"
        self.config_file = self.config_dir / "ssh_servers.json"
        self.config_dir.mkdir(exist_ok=True)
        self.servers = self._load_servers()
        self.current_server = self._load_current_server()
        
    def _load_servers(self) -> Dict:
        """Load saved SSH servers from config file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return data.get('servers', {})
            except:
                return {}
        return {}
        
    def _load_current_server(self) -> Optional[str]:
        """Load the currently selected server"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return data.get('current_server')
            except:
                pass
        return None
        
    def _save_config(self):
        """Save servers and current selection to config file"""
        data = {
            'servers': self.servers,
            'current_server': self.current_server,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def add_server(self, name: str, host: str, username: str, 
                   port: int = 22, key_path: Optional[str] = None) -> bool:
        """Add a new SSH server configuration"""
        if name in self.servers:
            return False  # Server already exists
            
        self.servers[name] = {
            'host': host,
            'username': username,
            'port': port,
            'key_path': key_path,
            'added': datetime.now().isoformat(),
            'last_used': None
        }
        
        # Set as current if it's the first server
        if not self.current_server:
            self.current_server = name
            
        self._save_config()
        return True
        
    def update_server(self, name: str, **kwargs) -> bool:
        """Update an existing server configuration"""
        if name not in self.servers:
            return False
            
        for key, value in kwargs.items():
            if key in ['host', 'username', 'port', 'key_path']:
                self.servers[name][key] = value
                
        self._save_config()
        return True
        
    def remove_server(self, name: str) -> bool:
        """Remove a server configuration"""
        if name not in self.servers:
            return False
            
        del self.servers[name]
        
        # Update current server if needed
        if self.current_server == name:
            self.current_server = list(self.servers.keys())[0] if self.servers else None
            
        self._save_config()
        return True
        
    def select_server(self, name: str) -> bool:
        """Select a server as current"""
        if name not in self.servers:
            return False
            
        self.current_server = name
        self.servers[name]['last_used'] = datetime.now().isoformat()
        self._save_config()
        return True
        
    def get_server(self, name: Optional[str] = None) -> Optional[Dict]:
        """Get server configuration"""
        server_name = name or self.current_server
        if server_name and server_name in self.servers:
            return {
                'name': server_name,
                **self.servers[server_name]
            }
        return None
        
    def list_servers(self) -> List[Dict]:
        """List all saved servers"""
        servers_list = []
        for name, config in self.servers.items():
            servers_list.append({
                'name': name,
                'current': name == self.current_server,
                **config
            })
        return sorted(servers_list, key=lambda x: x.get('last_used') or '', reverse=True)
        
    def get_current_server(self) -> Optional[Dict]:
        """Get the currently selected server"""
        return self.get_server(self.current_server)