#!/usr/bin/env python3
"""E2E test for echo > file.py command to verify pod and postgres sync"""

import asyncio
import sys
import os
import requests

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.container_manager import container_manager
from app.models.postgres_models import CodeSession, WorkspaceItem

BASE_URL = "http://localhost:8000"

async def test_echo_redirect_e2e():
    """Test that 'echo bro > file.py' creates/updates file in both pod and postgres"""

    print("=" * 70)
    print("E2E TEST: echo bro > file.py")
    print("=" * 70)

    # Step 1: Create a workspace via REST API
    print("\n1. Creating workspace via REST API...")
    response = requests.post(
        f"{BASE_URL}/api/sessions/",
        json={"user_id": 1, "name": "E2E Test Workspace"}
    )

    if response.status_code != 201:
        print(f"   ❌ Failed to create workspace: {response.text}")
        return False

    workspace_data = response.json()
    workspace_id = workspace_data["data"]["id"]  # This is the UUID
    print(f"   ✅ Workspace created with ID: {workspace_id}")

    # Step 2: Create session_id for container manager (matches websocket format)
    session_id = f"user_1_ws_{workspace_id}_123_456"
    print(f"\n2. Session ID for container: {session_id}")

    try:
        # Step 3: Initialize pod
        print("\n3. Initializing pod...")
        await container_manager.create_fresh_session(session_id)

        # Wait for pod to be ready
        for i in range(60):
            if container_manager.is_pod_ready(session_id):
                print(f"   ✅ Pod ready after {i+1} seconds")
                break
            await asyncio.sleep(1)
        else:
            print("   ❌ Pod failed to become ready")
            return False

        # Step 4: Run echo bro > file.py
        print("\n4. Running: echo bro > file.py")
        output, exit_code = await container_manager.execute_command(
            session_id,
            'echo "bro" > file.py'
        )
        print(f"   Output: {output}")
        print(f"   Exit code: {exit_code}")

        if exit_code != 0:
            print("   ❌ Command failed")
            return False

        # Step 5: Sync to database
        print("\n5. Syncing changes to database...")
        from app.websockets.handlers import sync_pod_changes_to_database
        await sync_pod_changes_to_database(session_id, 'echo "bro" > file.py')
        print("   ✅ Sync completed")

        # Wait a bit for sync to complete
        await asyncio.sleep(2)

        # Step 6: Verify in pod
        print("\n6. Verifying in pod with 'cat file.py'...")
        cat_output, cat_exit = await container_manager.execute_command(
            session_id,
            "cat file.py"
        )
        pod_content = cat_output.strip()
        print(f"   Pod content: '{pod_content}'")

        # Step 7: Verify in postgres
        print("\n7. Verifying in postgres...")
        session_db = CodeSession.get_by_uuid(workspace_id)
        if not session_db:
            print(f"   ❌ Session not found in database: {workspace_id}")
            return False

        items = WorkspaceItem.get_all_by_session(session_db.id)
        file_item = None
        for item in items:
            if item.name == "file.py" and item.type == "file":
                file_item = item
                break

        if file_item:
            db_content = file_item.content.strip() if file_item.content else ""
            print(f"   Postgres content: '{db_content}'")
        else:
            print(f"   ❌ File not found in postgres!")
            print(f"   Available items: {[(i.name, i.type) for i in items]}")
            db_content = None

        # Step 8: Verification
        print("\n8. Verification:")
        print("   " + "-" * 60)

        expected_content = "bro"
        pod_success = pod_content == expected_content
        db_success = db_content == expected_content

        print(f"   Expected: '{expected_content}'")
        print(f"   Pod:      '{pod_content}' {'✅' if pod_success else '❌'}")
        print(f"   Postgres: '{db_content}' {'✅' if db_success else '❌'}")

        # Step 9: Cleanup
        print("\n9. Cleaning up...")
        await container_manager.cleanup_session(session_id)
        print("   ✅ Pod cleaned up")

        # Final result
        print("\n" + "=" * 70)
        if pod_success and db_success:
            print("✅ TEST PASSED: echo redirect works correctly!")
            print("=" * 70)
            return True
        else:
            print("❌ TEST FAILED")
            if not pod_success:
                print(f"   - Pod mismatch: expected '{expected_content}', got '{pod_content}'")
            if not db_success:
                print(f"   - Postgres mismatch: expected '{expected_content}', got '{db_content}'")
            print("=" * 70)
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

        # Cleanup
        try:
            await container_manager.cleanup_session(session_id)
        except:
            pass

        return False

if __name__ == "__main__":
    success = asyncio.run(test_echo_redirect_e2e())
    sys.exit(0 if success else 1)
