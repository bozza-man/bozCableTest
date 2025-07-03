#!/bin/bash

echo "🔄 Sending reload command to backend..."

# Use Python to send WebSocket command
python3 -c "
import asyncio
import websockets
import json

async def reload():
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            await ws.send(json.dumps({'type': 'reload_backend'}))
            response = await ws.recv()
            data = json.loads(response)
            
            if data.get('type') == 'reload_status':
                if data.get('status') == 'complete':
                    print('✅ Backend reloaded successfully!')
                else:
                    print(f'Status: {data.get(\"message\", \"Unknown\")}')
    except Exception as e:
        print(f'❌ Error: {e}')

asyncio.run(reload())
"