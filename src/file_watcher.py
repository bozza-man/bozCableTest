#!/usr/bin/env python3
"""
File watcher for automatic code reloading
"""

import os
import time
import asyncio
import websockets
import json
from pathlib import Path
from typing import Dict, Set
import hashlib

class FileWatcher:
    def __init__(self, watch_dir='src', extensions=('.py',)):
        self.watch_dir = Path(watch_dir)
        self.extensions = extensions
        self.file_hashes: Dict[Path, str] = {}
        self.websocket = None
        self.running = True
        
    def calculate_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of file content"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def scan_files(self) -> Dict[Path, str]:
        """Scan all Python files and return their hashes"""
        files = {}
        for ext in self.extensions:
            for filepath in self.watch_dir.rglob(f'*{ext}'):
                if filepath.is_file() and not filepath.name.startswith('.'):
                    try:
                        files[filepath] = self.calculate_hash(filepath)
                    except:
                        pass
        return files
    
    def detect_changes(self) -> Set[Path]:
        """Detect which files have changed"""
        current_files = self.scan_files()
        changed = set()
        
        # Check for modified files
        for filepath, new_hash in current_files.items():
            old_hash = self.file_hashes.get(filepath)
            if old_hash != new_hash:
                changed.add(filepath)
        
        # Check for deleted files
        for filepath in self.file_hashes:
            if filepath not in current_files:
                changed.add(filepath)
        
        # Update stored hashes
        self.file_hashes = current_files
        
        return changed
    
    async def connect_backend(self):
        """Connect to backend WebSocket"""
        uri = "ws://localhost:8765"
        try:
            self.websocket = await websockets.connect(uri)
            print(f"✅ Connected to backend at {uri}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def send_reload_command(self):
        """Send reload command to backend"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps({'type': 'reload_backend'}))
                
                # Wait for response
                response = await asyncio.wait_for(self.websocket.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get('type') == 'reload_status':
                    status = data.get('status')
                    if status == 'complete':
                        return True
            except:
                pass
        return False
    
    async def watch_loop(self):
        """Main watch loop"""
        print("🔍 File watcher started")
        print(f"Watching directory: {self.watch_dir.absolute()}")
        print(f"File extensions: {self.extensions}")
        print("")
        
        # Initial scan
        self.file_hashes = self.scan_files()
        print(f"Monitoring {len(self.file_hashes)} files")
        
        # Connect to backend
        if not await self.connect_backend():
            print("Cannot connect to backend. Please ensure it's running.")
            return
        
        last_reload = 0
        reload_cooldown = 2  # seconds
        
        while self.running:
            try:
                changed = self.detect_changes()
                
                if changed:
                    # Apply cooldown to prevent rapid reloads
                    current_time = time.time()
                    if current_time - last_reload < reload_cooldown:
                        await asyncio.sleep(reload_cooldown - (current_time - last_reload))
                    
                    print(f"\n🔄 Detected changes in {len(changed)} file(s):")
                    for filepath in changed:
                        print(f"   • {filepath.relative_to(self.watch_dir.parent)}")
                    
                    print("Reloading backend...")
                    if await self.send_reload_command():
                        print("✅ Backend reloaded successfully!")
                    else:
                        print("❌ Backend reload failed")
                        # Try to reconnect
                        await self.websocket.close()
                        await self.connect_backend()
                    
                    last_reload = time.time()
                
                await asyncio.sleep(1)  # Check every second
                
            except KeyboardInterrupt:
                print("\n\nStopping file watcher...")
                self.running = False
            except Exception as e:
                print(f"\nError in watch loop: {e}")
                await asyncio.sleep(5)
        
        if self.websocket:
            await self.websocket.close()

async def main():
    import argparse
    parser = argparse.ArgumentParser(description='File watcher for automatic reloading')
    parser.add_argument('--dir', default='src', help='Directory to watch')
    parser.add_argument('--ext', default='.py', help='File extension to watch')
    args = parser.parse_args()
    
    watcher = FileWatcher(watch_dir=args.dir, extensions=(args.ext,))
    await watcher.watch_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ File watcher stopped")