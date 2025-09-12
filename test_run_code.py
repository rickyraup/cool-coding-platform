#!/usr/bin/env python3

import asyncio
import websockets
import json

async def test_run_code():
    uri = "ws://localhost:8001/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Wait for connection established message
            connection_msg = await websocket.recv()
            print(f"📥 Connection: {connection_msg}")
            
            # Send the exact code execution message that the UI sends
            code_content = """# Welcome to your new Python workspace!
# This is your main script file.

print("Hello, World!")

# You can write your Python code here
# Use the terminal to run this file with: python script.py
"""
            
            run_code_command = {
                "type": "code_execution",
                "sessionId": "34",
                "code": code_content,
                "filename": "main.py"
            }
            
            await websocket.send(json.dumps(run_code_command))
            print(f"📤 Sent run code command")
            
            # Wait for terminal output
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                print(f"📥 Terminal Output: {response}")
                
                data = json.loads(response)
                if data.get("type") == "terminal_output":
                    print(f"✅ SUCCESS: Got output: {data.get('output')}")
                else:
                    print(f"❌ Unexpected response type: {data.get('type')}")
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for terminal output")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Run Code functionality...")
    asyncio.run(test_run_code())