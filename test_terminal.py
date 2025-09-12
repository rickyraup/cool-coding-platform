#!/usr/bin/env python3

import asyncio
import websockets
import json

async def test_terminal():
    uri = "ws://localhost:8001/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Send a simple Python command
            test_command = {
                "type": "terminal_input",
                "sessionId": "34",
                "command": "python -c \"print('Hello from terminal test!')\""
            }
            
            await websocket.send(json.dumps(test_command))
            print(f"📤 Sent command: {test_command}")
            
            # Wait for multiple responses
            for i in range(3):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    print(f"📥 Response {i+1}: {response}")
                    
                    # Parse and display the response
                    data = json.loads(response)
                    print(f"📋 Parsed response {i+1}: {data}")
                    
                    # If this is the connection message, keep waiting for terminal output
                    if data.get("type") == "connection_established":
                        print("🔄 Connection confirmed, waiting for command output...")
                        continue
                        
                except asyncio.TimeoutError:
                    print(f"⏰ Timeout waiting for response {i+1}")
                    break
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing terminal functionality...")
    asyncio.run(test_terminal())