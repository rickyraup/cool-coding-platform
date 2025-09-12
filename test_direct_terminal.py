#!/usr/bin/env python3

import asyncio
import websockets
import json
import time

async def test_persistent_connection():
    uri = "ws://localhost:8001/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Wait for connection established message
            connection_msg = await websocket.recv()
            print(f"📥 Connection: {connection_msg}")
            
            # Send a terminal command (as if typed in terminal)
            terminal_command = {
                "type": "terminal_input",
                "sessionId": "34",
                "command": "echo 'Testing terminal input'"
            }
            
            await websocket.send(json.dumps(terminal_command))
            print(f"📤 Sent terminal command")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                print(f"📥 Terminal Response: {response}")
                
                data = json.loads(response)
                if data.get("type") == "terminal_output":
                    print(f"✅ SUCCESS: Terminal output: {data.get('output')}")
                else:
                    print(f"❌ Unexpected response: {data}")
                    
                # Keep connection alive and test again
                print("🕒 Keeping connection alive for 5 seconds...")
                await asyncio.sleep(5)
                
                # Test Run Code command after connection is stable
                print("\n🚀 Now testing Run Code command...")
                run_code = {
                    "type": "code_execution",
                    "sessionId": "34",
                    "code": "print('Code execution test!')",
                    "filename": "test.py"
                }
                
                await websocket.send(json.dumps(run_code))
                print(f"📤 Sent run code command")
                
                # Wait for run code response
                code_response = await asyncio.wait_for(websocket.recv(), timeout=10)
                print(f"📥 Code Response: {code_response}")
                
                code_data = json.loads(code_response)
                if code_data.get("type") == "terminal_output":
                    print(f"✅ SUCCESS: Code output: {code_data.get('output')}")
                else:
                    print(f"❌ Unexpected code response: {code_data}")
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for response")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing persistent terminal connection...")
    asyncio.run(test_persistent_connection())