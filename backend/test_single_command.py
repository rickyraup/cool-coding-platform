#!/usr/bin/env python3
"""Test single WebSocket command to debug the issue."""

import asyncio
import json
from typing import Optional

import websockets


async def test_single_command() -> Optional[bool]:
    """Test a single command to see exactly what happens."""
    uri = "ws://localhost:8001/ws"

    try:
        print("🔌 Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")

            # Wait for connection confirmation
            response = await websocket.recv()
            connection_msg = json.loads(response)
            print(f"📨 Connection: {connection_msg.get('message')}")

            # Send a simple command
            command = "echo 'hello world'"
            print(f"\n💻 Testing command: {command}")

            message = {
                "type": "terminal_input",
                "sessionId": "debug-session",
                "command": command,
            }

            print(f"📤 Sending: {message}")
            await websocket.send(json.dumps(message))

            # Receive response
            print("📥 Waiting for response...")
            response = await websocket.recv()
            result = json.loads(response)

            print(f"✅ Response received: {result}")

            if result.get("type") == "terminal_output":
                output = result.get("output", "")
                return_code = result.get("return_code", -1)
                print(f"Command output (code {return_code}):")
                print(output)
            else:
                print(f"Unexpected response type: {result.get('type')}")

            return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Testing single WebSocket command...\n")
    success = asyncio.run(test_single_command())
    print(f"\n{'✅ Success' if success else '❌ Failed'}")
