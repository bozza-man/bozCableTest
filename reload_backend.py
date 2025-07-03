#!/usr/bin/env python3
"""
Send reload command to the backend server
"""

import asyncio
import websockets
import json
import sys

async def reload_backend():
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to backend server")
            
            # Send reload command
            await websocket.send(json.dumps({'type': 'reload_backend'}))
            print("Sent reload command")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'reload_status':
                status = data.get('status')
                message = data.get('message', '')
                
                if status == 'complete':
                    print(f"✅ {message}")
                elif status == 'failed':
                    print(f"❌ {message}")
                else:
                    print(f"ℹ️  {message}")
                    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔄 Reloading backend server...")
    asyncio.run(reload_backend())