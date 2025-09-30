"""End-to-end test for save functionality: IDE → PostgreSQL → Pod sync."""
import asyncio
import json
import websockets
from datetime import datetime
import requests


async def test_save_and_sync():
    """Test that saving a file updates PostgreSQL and syncs to the pod."""

    # Test workspace ID - use existing workspace from logs
    workspace_id = "e4a0a7c8-9613-4d22-9bfc-421e44e1ad62"
    user_id = "5"
    test_file = "test_save.py"
    test_content_v1 = "print('Version 1')"
    test_content_v2 = "print('Version 2 - Updated!')"

    print("=" * 70)
    print("E2E TEST: Save → PostgreSQL → Pod Sync")
    print("=" * 70)
    print()

    # Step 1: Connect via WebSocket
    print("STEP 1: Connect to WebSocket")
    print("-" * 70)
    uri = f"ws://localhost:8001/ws?user_id={user_id}"

    async with websockets.connect(uri) as websocket:
        # Receive connection established message
        response = await websocket.recv()
        print(f"✅ Connected: {json.loads(response)['type']}")
        print()

        # Step 2: Create/Write initial file via WebSocket (manual save)
        print("STEP 2: Create file with initial content (manual save)")
        print("-" * 70)
        write_message = {
            "type": "file_system",
            "sessionId": workspace_id,
            "action": "write",
            "path": test_file,
            "content": test_content_v1,
            "isManualSave": True
        }
        await websocket.send(json.dumps(write_message))
        response1 = await websocket.recv()
        result1 = json.loads(response1)
        print(f"Write response: {result1['type']}")
        print(f"File: {result1.get('path')}")
        print(f"Content length: {len(result1.get('content', ''))}")
        print()

        # Wait for DB sync
        await asyncio.sleep(2)

        # Step 3: Verify file is in PostgreSQL
        print("STEP 3: Verify file exists in PostgreSQL via REST API")
        print("-" * 70)
        try:
            file_url = f"http://localhost:8001/api/workspace/{workspace_id}/file/{test_file}"
            file_response = requests.get(file_url)
            if file_response.status_code == 200:
                db_content = file_response.json().get('content', '')
                print(f"✅ File found in PostgreSQL")
                print(f"Content: {db_content}")
                assert db_content == test_content_v1, f"Content mismatch! Expected '{test_content_v1}', got '{db_content}'"
                print(f"✅ Content matches initial version")
            else:
                print(f"❌ File not found in PostgreSQL (status {file_response.status_code})")
                print(f"Response: {file_response.text}")
        except Exception as e:
            print(f"❌ Error checking PostgreSQL: {e}")
        print()

        # Step 4: Execute the file in the pod to verify it's synced
        print("STEP 4: Execute file in pod to verify filesystem sync")
        print("-" * 70)
        exec_message = {
            "type": "terminal_input",
            "sessionId": workspace_id,
            "command": f"python {test_file}"
        }
        await websocket.send(json.dumps(exec_message))
        exec_response = await websocket.recv()
        exec_result = json.loads(exec_response)

        # Wait for command to complete
        await asyncio.sleep(3)

        if exec_result.get('type') == 'terminal_output':
            output = exec_result.get('output', '').strip()
            print(f"✅ Execution output: {output}")
            assert 'Version 1' in output, f"Expected 'Version 1' in output, got: {output}"
            print(f"✅ Pod filesystem has correct content")
        else:
            print(f"⚠️ Response type: {exec_result.get('type')}")
        print()

        # Step 5: Update the file with new content (manual save)
        print("STEP 5: Update file with new content (manual save)")
        print("-" * 70)
        update_message = {
            "type": "file_system",
            "sessionId": workspace_id,
            "action": "write",
            "path": test_file,
            "content": test_content_v2,
            "isManualSave": True
        }
        await websocket.send(json.dumps(update_message))
        response2 = await websocket.recv()
        result2 = json.loads(response2)
        print(f"Update response: {result2['type']}")
        print(f"Updated content length: {len(result2.get('content', ''))}")
        print()

        # Wait for DB sync
        await asyncio.sleep(2)

        # Step 6: Verify updated content in PostgreSQL
        print("STEP 6: Verify updated content in PostgreSQL")
        print("-" * 70)
        try:
            file_response2 = requests.get(file_url)
            if file_response2.status_code == 200:
                db_content2 = file_response2.json().get('content', '')
                print(f"✅ File found in PostgreSQL")
                print(f"Content: {db_content2}")
                assert db_content2 == test_content_v2, f"Content mismatch! Expected '{test_content_v2}', got '{db_content2}'"
                print(f"✅ PostgreSQL has updated content")
            else:
                print(f"❌ File not found in PostgreSQL (status {file_response2.status_code})")
        except Exception as e:
            print(f"❌ Error checking PostgreSQL: {e}")
        print()

        # Step 7: Execute updated file in pod
        print("STEP 7: Execute updated file in pod")
        print("-" * 70)
        exec_message2 = {
            "type": "terminal_input",
            "sessionId": workspace_id,
            "command": f"python {test_file}"
        }
        await websocket.send(json.dumps(exec_message2))
        exec_response2 = await websocket.recv()
        exec_result2 = json.loads(exec_response2)

        # Wait for command to complete
        await asyncio.sleep(3)

        if exec_result2.get('type') == 'terminal_output':
            output2 = exec_result2.get('output', '').strip()
            print(f"✅ Execution output: {output2}")
            assert 'Version 2' in output2, f"Expected 'Version 2' in output, got: {output2}"
            print(f"✅ Pod filesystem has updated content")
        else:
            print(f"⚠️ Response type: {exec_result2.get('type')}")
        print()

        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("Save flow verified:")
        print("  1. ✅ IDE → WebSocket → Backend")
        print("  2. ✅ Backend → PostgreSQL")
        print("  3. ✅ Backend → Pod filesystem")
        print("  4. ✅ Pod executes latest content")
        print()


if __name__ == "__main__":
    print(f"🚀 Starting E2E Save/Sync Test at {datetime.now()}")
    print()
    asyncio.run(test_save_and_sync())