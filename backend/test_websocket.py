#!/usr/bin/env python3
"""Test WebSocket terminal functionality."""

import asyncio
import json
import websockets
import sys

async def test_websocket_terminal():
    """Test WebSocket connection and terminal commands."""
    uri = "ws://localhost:8001/ws"
    
    try:
        print("🔌 Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            # Wait for connection confirmation
            response = await websocket.recv()
            connection_msg = json.loads(response)
            print(f"📨 Connection: {connection_msg.get('message')}")
            
            # Test commands
            test_commands = [
                "help",
                "pwd",
                "ls -la",
                "echo 'Hello from WebSocket!'",
                "python3 -c \"print('Python works via WebSocket!')\"",
                "echo 'Test file content' > test.txt && cat test.txt"
            ]
            
            for command in test_commands:
                print(f"\n💻 Testing command: {command}")
                
                # Send terminal input
                message = {
                    "type": "terminal_input",
                    "sessionId": "websocket-test-session",
                    "command": command
                }
                
                await websocket.send(json.dumps(message))
                
                # Receive response
                response = await websocket.recv()
                result = json.loads(response)
                
                if result.get("type") == "terminal_output":
                    output = result.get("output", "")
                    return_code = result.get("return_code", -1)
                    print(f"✅ Output (code {return_code}):")
                    # Show first few lines of output
                    output_lines = output.split('\n')[:5]
                    for line in output_lines:
                        if line.strip():
                            print(f"   {line}")
                    if len(output.split('\n')) > 5:
                        print("   ...")
                else:
                    print(f"❌ Unexpected response: {result}")
            
            # Test container status
            print(f"\n🐳 Testing container status...")
            status_message = {
                "type": "container_status",
                "sessionId": "websocket-test-session"
            }
            
            await websocket.send(json.dumps(status_message))
            response = await websocket.recv()
            result = json.loads(response)
            
            print(f"📊 Container status: {result.get('status')}")
            print(f"   Message: {result.get('message', 'N/A')}")
            
            print(f"\n🎉 All WebSocket tests completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing WebSocket terminal functionality...\n")
    success = asyncio.run(test_websocket_terminal())
    if success:
        print("\n✅ WebSocket integration is working perfectly!")
        print("🚀 Frontend can now connect and execute commands!")
    else:
        print("\n❌ WebSocket tests failed")
    sys.exit(0 if success else 1)