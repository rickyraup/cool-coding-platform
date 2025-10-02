#!/usr/bin/env python3
"""
End-to-end test for echo > file.py command
Tests that the file is created in both the pod and postgres
"""

import asyncio
import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.postgres_models import CodeSession, WorkspaceItem
from app.services.container_manager import container_manager


async def test_echo_redirect():
    """Test that echo > file.py creates file in pod and syncs to postgres"""

    print("\n" + "="*70)
    print("E2E TEST: echo bro > test_file.py")
    print("="*70)

    # Create a test session with a valid UUID
    test_session_uuid = str(uuid.uuid4())
    test_session_id = f"user_test_ws_{test_session_uuid}_123_456"

    print(f"Test session UUID: {test_session_uuid}")
    print(f"Test session ID: {test_session_id}")

    try:
        # Step 1: Clean up any existing test session
        print("\n1. Cleaning up existing test data...")
        existing_session = CodeSession.get_by_uuid(test_session_uuid)
        if existing_session:
            # Delete workspace items
            items = WorkspaceItem.get_all_by_session(existing_session.id)
            for item in items:
                item.delete()
            existing_session.delete()
        print("   ✓ Cleanup complete")

        # Step 2: Create a fresh session in postgres
        print("\n2. Creating test session in postgres...")
        session_db = CodeSession.create(uuid=test_session_uuid)
        print(f"   ✓ Session created: {session_db.id} ({session_db.uuid})")

        # Step 3: Create a pod for the session
        print("\n3. Creating pod for session...")
        await container_manager.create_fresh_session(test_session_id)
        print(f"   ✓ Pod created for session: {test_session_id}")

        # Wait for pod to be ready
        print("\n4. Waiting for pod to be ready...")
        max_wait = 60  # 60 seconds
        for i in range(max_wait):
            if container_manager.is_pod_ready(test_session_id):
                print(f"   ✓ Pod ready after {i+1} seconds")
                break
            await asyncio.sleep(1)
        else:
            print("   ✗ Pod failed to become ready")
            return False

        # Step 5: Execute echo command
        print("\n5. Executing: echo bro > test_file.py")
        output, exit_code = await container_manager.execute_command(
            test_session_id,
            'echo "bro" > test_file.py'
        )
        print(f"   Output: {output}")
        print(f"   Exit code: {exit_code}")

        if exit_code != 0:
            print("   ✗ Command failed")
            return False
        print("   ✓ Command executed successfully")

        # Step 6: Sync pod changes to database
        print("\n6. Syncing pod changes to postgres...")
        from app.websockets.handlers import sync_pod_changes_to_database
        await sync_pod_changes_to_database(test_session_id, "echo bro > test_file.py")
        print("   ✓ Sync completed")

        # Step 7: Verify file exists in pod
        print("\n7. Verifying file exists in pod...")
        ls_output, ls_exit = await container_manager.execute_command(
            test_session_id,
            "ls -la /app/test_file.py"
        )
        if ls_exit == 0:
            print(f"   ✓ File exists in pod: {ls_output.strip()}")
        else:
            print(f"   ✗ File not found in pod")
            return False

        # Step 8: Verify file content in pod
        print("\n8. Verifying file content in pod...")
        cat_output, cat_exit = await container_manager.execute_command(
            test_session_id,
            "cat /app/test_file.py"
        )
        if cat_exit == 0:
            print(f"   Content: '{cat_output.strip()}'")
            if cat_output.strip() == "bro":
                print("   ✓ Content matches expected value")
            else:
                print(f"   ✗ Content mismatch. Expected 'bro', got '{cat_output.strip()}'")
                return False
        else:
            print("   ✗ Failed to read file content")
            return False

        # Step 9: Verify file exists in postgres
        print("\n9. Verifying file exists in postgres...")
        items = WorkspaceItem.get_all_by_session(session_db.id)
        test_file = None
        for item in items:
            if item.name == "test_file.py" and item.type == "file":
                test_file = item
                break

        if test_file:
            print(f"   ✓ File found in postgres: {test_file.name}")
        else:
            print("   ✗ File not found in postgres")
            print(f"   Available files: {[item.name for item in items]}")
            return False

        # Step 10: Verify file content in postgres
        print("\n10. Verifying file content in postgres...")
        if test_file.content.strip() == "bro":
            print(f"    ✓ Content matches: '{test_file.content.strip()}'")
        else:
            print(f"    ✗ Content mismatch. Expected 'bro', got '{test_file.content.strip()}'")
            return False

        # Step 11: Cleanup
        print("\n11. Cleaning up...")
        await container_manager.cleanup_session(test_session_id)
        test_file.delete()
        session_db.delete()
        print("   ✓ Cleanup complete")

        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70)
        return True

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        # Cleanup on failure
        try:
            await container_manager.cleanup_session(test_session_id)
            existing_session = CodeSession.get_by_uuid(test_session_uuid)
            if existing_session:
                items = WorkspaceItem.get_all_by_session(existing_session.id)
                for item in items:
                    item.delete()
                existing_session.delete()
        except:
            pass

        return False


if __name__ == "__main__":
    result = asyncio.run(test_echo_redirect())
    sys.exit(0 if result else 1)
