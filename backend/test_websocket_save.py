#!/usr/bin/env python3
"""
Test WebSocket save path to ensure sync works for manual saves via the UI.
"""

import asyncio
import json
import websockets
import requests

# Test configuration
WS_URL = "ws://localhost:8001/ws"
SESSION_UUID = "106f0305-c080-4ba9-a64e-f8a7a102286f"
TEST_FILENAME = "test_websocket_save.py"
TEST_CONTENT = '''# WebSocket save test
print("This content was saved via WebSocket!")
print("Testing sync to Docker container...")
x = 42
print(f"Answer: {x}")
'''

async def test_websocket_save():
    """Test save via WebSocket like the frontend does."""

    print("🔗 Testing WebSocket save functionality...")

    try:
        # Connect to WebSocket
        async with websockets.connect(WS_URL) as websocket:
            print("✅ Connected to WebSocket")

            # Send a file save message (like the frontend does)
            save_message = {
                "type": "file_system",
                "sessionId": SESSION_UUID,
                "action": "write",
                "path": TEST_FILENAME,
                "content": TEST_CONTENT,
                "isManualSave": True  # This is the critical flag
            }

            print(f"📤 Sending save message for {TEST_FILENAME}...")
            await websocket.send(json.dumps(save_message))

            # Receive connection acknowledgment
            response1 = await websocket.recv()
            response1_data = json.loads(response1)
            print(f"📥 Connection response: {response1_data.get('message', 'No message')}")

            # Receive actual save response
            response2 = await websocket.recv()
            response2_data = json.loads(response2)
            print(f"📥 Save response: {response2_data.get('message', 'No message')}")

            if response2_data.get("type") == "file_system" and response2_data.get("action") == "write":
                print("✅ WebSocket save completed successfully")
                return True
            else:
                print(f"❌ Unexpected save response: {response2_data}")
                return False

    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

def verify_sync_to_docker():
    """Verify the saved file is accessible in Docker container."""
    print("\n🐳 Verifying sync to Docker container...")

    try:
        # Check filesystem
        filesystem_path = f"/tmp/coding_platform_sessions/workspace_{SESSION_UUID}/{TEST_FILENAME}"
        with open(filesystem_path, 'r') as f:
            filesystem_content = f.read()

        print(f"📁 Filesystem content: {len(filesystem_content)} characters")

        # Check Docker container
        import subprocess
        result = subprocess.run([
            "docker", "ps", "--filter", f"name=.*{SESSION_UUID}.*", "--format", "{{.ID}}"
        ], capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            container_id = result.stdout.strip().split('\n')[0]
            print(f"🐳 Found container: {container_id}")

            # Read from container
            docker_result = subprocess.run([
                "docker", "exec", container_id, "cat", f"/app/{TEST_FILENAME}"
            ], capture_output=True, text=True)

            if docker_result.returncode == 0:
                docker_content = docker_result.stdout
                print(f"🐳 Docker content: {len(docker_content)} characters")

                # Compare content
                if filesystem_content.strip() == docker_content.strip() == TEST_CONTENT.strip():
                    print("✅ SUCCESS: All content matches!")
                    print("🔄 WebSocket save sync is working correctly!")
                    return True
                else:
                    print("❌ FAILURE: Content mismatch")
                    print(f"Expected: {repr(TEST_CONTENT.strip())}")
                    print(f"Filesystem: {repr(filesystem_content.strip())}")
                    print(f"Docker: {repr(docker_content.strip())}")
                    return False
            else:
                print(f"❌ Failed to read from Docker: {docker_result.stderr}")
                return False
        else:
            print("❌ No Docker container found for session")
            return False

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🧪 Testing WebSocket-based save sync to Docker container")
    print("=" * 60)

    # Test WebSocket save
    websocket_success = await test_websocket_save()

    if websocket_success:
        # Wait a moment for sync
        await asyncio.sleep(1)

        # Verify sync to Docker
        sync_success = verify_sync_to_docker()

        print("\n" + "=" * 60)
        if sync_success:
            print("🎉 ALL TESTS PASSED: WebSocket save sync is working!")
        else:
            print("💥 TEST FAILED: WebSocket save sync has issues")
        print("=" * 60)
    else:
        print("\n💥 WebSocket save test failed - cannot proceed with sync verification")

if __name__ == "__main__":
    asyncio.run(main())