"""
End-to-end test for touch and rm commands.
Tests that the commands properly sync with database and pods.
"""
import asyncio
import os
import sys
import uuid

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.container_manager import container_manager
from app.models.postgres_models import CodeSession, WorkspaceItem


async def test_touch_command():
    """Test touch command end-to-end"""
    print("\n" + "="*60)
    print("Testing TOUCH command")
    print("="*60)

    # Create a test workspace
    workspace_id = str(uuid.uuid4())
    session_id = f"user_test_ws_{workspace_id}_{int(asyncio.get_event_loop().time())}_test"

    print(f"\n1. Creating test workspace: {workspace_id}")

    # Create database session
    session_db = CodeSession.create(uuid=workspace_id)
    print(f"✓ Created database session with ID: {session_db.id}")

    # Create pod
    print(f"\n2. Creating Kubernetes pod for session: {session_id}")
    try:
        await container_manager.create_fresh_session(session_id)
        print(f"✓ Pod created successfully")
    except Exception as e:
        print(f"✗ Failed to create pod: {e}")
        return False

    # Wait for pod to be ready
    print("\n3. Waiting for pod to be ready...")
    await asyncio.sleep(3)

    # Test touch command
    test_filename = "test_touch_file.py"
    print(f"\n4. Running touch command: touch {test_filename}")

    from app.websockets.handlers import handle_touch_command

    class MockWebSocket:
        async def send_json(self, data):
            print(f"   WebSocket message sent: {data.get('type')}")

    websocket = MockWebSocket()
    result = await handle_touch_command(f"touch {test_filename}", session_id, websocket)
    print(f"   Touch result: {result}")

    # Check if file exists in database
    print(f"\n5. Checking if file exists in database...")
    items = WorkspaceItem.get_all_by_session(session_db.id)
    file_in_db = any(item.name == test_filename and item.type == "file" for item in items)

    if file_in_db:
        print(f"✓ File '{test_filename}' found in database")
    else:
        print(f"✗ File '{test_filename}' NOT found in database")
        print(f"   Found items: {[item.name for item in items]}")
        return False

    # Check if file exists in pod
    print(f"\n6. Checking if file exists in pod...")
    output, exit_code = await container_manager.execute_command(session_id, f"ls -la /app/{test_filename}")

    if exit_code == 0:
        print(f"✓ File '{test_filename}' found in pod")
        print(f"   ls output: {output}")
    else:
        print(f"✗ File '{test_filename}' NOT found in pod")
        print(f"   ls output: {output}")

        # Debug: Check what files exist in /app
        print("\n   Debug: Listing all files in /app")
        ls_output, _ = await container_manager.execute_command(session_id, "ls -la /app")
        print(f"   Files in /app:\n{ls_output}")
        return False

    # Cleanup pod
    print(f"\n7. Cleaning up pod...")
    await container_manager.cleanup_session(session_id)

    print("\n✓ TOUCH command test PASSED")
    return True


async def test_rm_command():
    """Test rm command end-to-end"""
    print("\n" + "="*60)
    print("Testing RM command")
    print("="*60)

    # Create a test workspace
    workspace_id = str(uuid.uuid4())
    session_id = f"user_test_ws_{workspace_id}_{int(asyncio.get_event_loop().time())}_test"

    print(f"\n1. Creating test workspace: {workspace_id}")

    # Create database session
    session_db = CodeSession.create(uuid=workspace_id)
    print(f"✓ Created database session with ID: {session_db.id}")

    # Create a file in database
    test_filename = "test_rm_file.py"
    print(f"\n2. Creating test file in database: {test_filename}")
    WorkspaceItem.create(
        session_id=session_db.id,
        parent_id=None,
        name=test_filename,
        item_type="file",
        content="# This file will be deleted",
    )
    print(f"✓ File created in database")

    # Sync file to filesystem
    print(f"\n3. Syncing file to filesystem...")
    from app.api.workspace_files import sync_file_to_filesystem
    sync_file_to_filesystem(workspace_id, test_filename, "# This file will be deleted")
    print(f"✓ File synced to filesystem")

    # Create pod
    print(f"\n4. Creating Kubernetes pod for session: {session_id}")
    try:
        await container_manager.create_fresh_session(session_id)
        print(f"✓ Pod created successfully")
    except Exception as e:
        print(f"✗ Failed to create pod: {e}")
        return False

    # Wait for pod to be ready
    print("\n5. Waiting for pod to be ready...")
    await asyncio.sleep(3)

    # Verify file exists in pod before deletion
    print(f"\n6. Verifying file exists in pod before deletion...")
    output, exit_code = await container_manager.execute_command(session_id, f"ls -la /app/{test_filename}")

    if exit_code == 0:
        print(f"✓ File '{test_filename}' exists in pod before deletion")
    else:
        print(f"✗ File '{test_filename}' does NOT exist in pod (should exist before deletion)")
        print(f"   ls output: {output}")

        # Debug
        print("\n   Debug: Listing all files in /app")
        ls_output, _ = await container_manager.execute_command(session_id, "ls -la /app")
        print(f"   Files in /app:\n{ls_output}")

    # Test rm command
    print(f"\n7. Running rm command: rm {test_filename}")

    from app.websockets.handlers import handle_rm_command

    class MockWebSocket:
        async def send_json(self, data):
            print(f"   WebSocket message sent: {data.get('type')}")

    websocket = MockWebSocket()
    result = await handle_rm_command(f"rm {test_filename}", session_id, websocket)
    print(f"   rm result: {result}")

    # Check if file was deleted from database
    print(f"\n8. Checking if file was deleted from database...")
    items = WorkspaceItem.get_all_by_session(session_db.id)
    file_in_db = any(item.name == test_filename and item.type == "file" for item in items)

    if not file_in_db:
        print(f"✓ File '{test_filename}' successfully deleted from database")
    else:
        print(f"✗ File '{test_filename}' still exists in database (should be deleted)")
        return False

    # Check if file was deleted from pod
    print(f"\n9. Checking if file was deleted from pod...")
    output, exit_code = await container_manager.execute_command(session_id, f"ls -la /app/{test_filename}")

    if exit_code != 0:
        print(f"✓ File '{test_filename}' successfully deleted from pod")
    else:
        print(f"✗ File '{test_filename}' still exists in pod (should be deleted)")
        print(f"   ls output: {output}")
        return False

    # Cleanup pod
    print(f"\n10. Cleaning up pod...")
    await container_manager.cleanup_session(session_id)

    print("\n✓ RM command test PASSED")
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("END-TO-END TEST: Touch and rm Commands")
    print("="*60)

    # Test touch command
    touch_passed = await test_touch_command()

    # Test rm command
    rm_passed = await test_rm_command()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"TOUCH command: {'✓ PASSED' if touch_passed else '✗ FAILED'}")
    print(f"RM command:    {'✓ PASSED' if rm_passed else '✗ FAILED'}")
    print("="*60)

    if touch_passed and rm_passed:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
