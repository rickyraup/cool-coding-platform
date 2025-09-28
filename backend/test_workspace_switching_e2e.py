#!/usr/bin/env python3
"""
E2E Test for Workspace Switching Issue

Test case: User switches from workspace "test 1" to workspace "test"
and expects to see different files in each workspace via ls command.

Current issue: ls shows the same files in both workspaces instead of
workspace-specific files.
"""

import asyncio
import json
import websockets
from typing import Dict, Any
import time


class WorkspaceSwitchingTest:
    def __init__(self):
        self.websocket_url = "ws://localhost:8001/ws?user_id=5"
        self.websocket = None

    async def connect(self):
        """Connect to WebSocket"""
        self.websocket = await websockets.connect(self.websocket_url)
        print("✅ Connected to WebSocket")

        # Wait for connection confirmation
        response = await self.websocket.recv()
        print(f"📨 Connection response: {response}")

    async def send_terminal_command(self, session_id: str, command: str) -> Dict[str, Any]:
        """Send terminal command and get response"""
        message = {
            "type": "terminal_input",
            "sessionId": session_id,
            "command": command
        }

        await self.websocket.send(json.dumps(message))
        response = await self.websocket.recv()
        return json.loads(response)

    async def test_workspace_switching(self):
        """Test the exact scenario reported by user"""
        print("\n🧪 Starting Workspace Switching E2E Test")
        print("=" * 50)

        # Test workspace 1: "106f0305-c080-4ba9-a64e-f8a7a102286f" (test 1)
        workspace_1 = "106f0305-c080-4ba9-a64e-f8a7a102286f"

        # Test workspace 2: "8f4bed93-5b7e-43ad-b4a0-209fecda7bb6" (test)
        workspace_2 = "8f4bed93-5b7e-43ad-b4a0-209fecda7bb6"

        print(f"\n📂 Step 1: Connect to workspace 1 ({workspace_1})")
        print("Running 'ls' command...")

        response1 = await self.send_terminal_command(workspace_1, "ls")
        files_in_workspace_1 = response1.get("output", "").strip().split("\n")
        files_in_workspace_1 = [f for f in files_in_workspace_1 if f.strip()]

        print(f"🔍 Files in workspace 1: {files_in_workspace_1}")
        print(f"📝 Session ID: {response1.get('sessionId')}")

        # Small delay
        await asyncio.sleep(1)

        print(f"\n📂 Step 2: Switch to workspace 2 ({workspace_2})")
        print("Running 'ls' command...")

        response2 = await self.send_terminal_command(workspace_2, "ls")
        files_in_workspace_2 = response2.get("output", "").strip().split("\n")
        files_in_workspace_2 = [f for f in files_in_workspace_2 if f.strip()]

        print(f"🔍 Files in workspace 2: {files_in_workspace_2}")
        print(f"📝 Session ID: {response2.get('sessionId')}")

        # Analysis
        print(f"\n📊 Analysis:")
        print(f"Files in workspace 1: {files_in_workspace_1}")
        print(f"Files in workspace 2: {files_in_workspace_2}")

        if files_in_workspace_1 == files_in_workspace_2:
            print("❌ BUG CONFIRMED: Both workspaces show the same files!")
            print("   This indicates containers are not properly isolated between workspaces")
        else:
            print("✅ SUCCESS: Workspaces show different files as expected")

        # Additional test: Run ls again in workspace 1 to confirm persistence
        print(f"\n📂 Step 3: Switch back to workspace 1 ({workspace_1})")
        print("Running 'ls' command again to verify persistence...")

        response3 = await self.send_terminal_command(workspace_1, "ls")
        files_in_workspace_1_again = response3.get("output", "").strip().split("\n")
        files_in_workspace_1_again = [f for f in files_in_workspace_1_again if f.strip()]

        print(f"🔍 Files in workspace 1 (second time): {files_in_workspace_1_again}")
        print(f"📝 Session ID: {response3.get('sessionId')}")

        if files_in_workspace_1 == files_in_workspace_1_again:
            print("✅ Workspace 1 files are persistent")
        else:
            print("❌ Workspace 1 files changed between visits")

        # Container reuse analysis
        session_1_first = response1.get('sessionId')
        session_1_second = response3.get('sessionId')
        session_2 = response2.get('sessionId')

        print(f"\n🐳 Container Session Analysis:")
        print(f"Workspace 1 (first visit):  {session_1_first}")
        print(f"Workspace 2:                {session_2}")
        print(f"Workspace 1 (second visit): {session_1_second}")

        if session_1_first == session_1_second:
            print("✅ Container session properly reused for workspace 1")
        else:
            print("❌ New container session created when returning to workspace 1")

        print("\n" + "=" * 50)
        return {
            "workspace_1_files": files_in_workspace_1,
            "workspace_2_files": files_in_workspace_2,
            "files_same": files_in_workspace_1 == files_in_workspace_2,
            "session_reused": session_1_first == session_1_second
        }

    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 WebSocket connection closed")


async def main():
    """Run the E2E test"""
    test = WorkspaceSwitchingTest()

    try:
        await test.connect()
        results = await test.test_workspace_switching()

        print(f"\n📋 Test Results Summary:")
        print(f"Workspace isolation working: {not results['files_same']}")
        print(f"Container session reuse working: {results['session_reused']}")

        if results['files_same']:
            print("\n❌ WORKSPACE SWITCHING BUG CONFIRMED")
            print("   Expected: Different files in different workspaces")
            print("   Actual: Same files shown in both workspaces")
        else:
            print("\n✅ WORKSPACE SWITCHING WORKING CORRECTLY")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")

    finally:
        await test.close()


if __name__ == "__main__":
    asyncio.run(main())