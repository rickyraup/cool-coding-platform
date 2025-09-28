#!/usr/bin/env python3
"""
Test file deletion with active container session.
"""

import asyncio
import sys
import os
sys.path.append('/Users/rickyraup1/personal_projects/cool-coding-platform/backend')

from app.services.container_manager import container_manager
from app.services.workspace_loader import workspace_loader

SESSION_UUID = "106f0305-c080-4ba9-a64e-f8a7a102286f"
TEST_FILENAME = "test_container_deletion.py"

async def test_with_container():
    """Test file deletion with active container session."""
    print("🧪 Testing file deletion with active container session")
    print("=" * 60)

    try:
        # Step 1: Create a container session
        print(f"🔧 Creating container session for {SESSION_UUID}...")
        container_session = await container_manager.get_or_create_session(SESSION_UUID)
        print(f"✅ Container session created with working dir: {container_session.working_dir}")

        # Step 2: Create test file in workspace and container
        print(f"📝 Creating test file: {TEST_FILENAME}")

        # Create file in mounted volume (filesystem sync location)
        workspace_dir = f"/tmp/coding_platform_sessions/workspace_{SESSION_UUID}"
        os.makedirs(workspace_dir, exist_ok=True)
        test_file_path = os.path.join(workspace_dir, TEST_FILENAME)

        with open(test_file_path, 'w') as f:
            f.write("# Test file for container deletion\nprint('This should be deleted from container')\n")

        # Create file in container working directory
        container_file_path = os.path.join(container_session.working_dir, TEST_FILENAME)
        with open(container_file_path, 'w') as f:
            f.write("# Test file for container deletion\nprint('This should be deleted from container')\n")

        print(f"✅ Created test file in both locations")
        print(f"  📁 Workspace: {test_file_path}")
        print(f"  🐳 Container: {container_file_path}")

        # Step 3: Verify files exist
        workspace_exists = os.path.exists(test_file_path)
        container_exists = os.path.exists(container_file_path)
        print(f"📋 Before deletion - Workspace: {workspace_exists}, Container: {container_exists}")

        # Step 4: Get session ID for deletion
        from app.models.postgres_models import CodeSession
        session = CodeSession.get_by_uuid(SESSION_UUID)
        if not session:
            print(f"❌ Session not found in database")
            return False

        # Step 5: Test deletion via workspace_loader
        print(f"🗑️ Testing deletion via workspace_loader...")
        delete_success = await workspace_loader.delete_workspace_file(session.id, TEST_FILENAME)
        print(f"📊 Deletion result: {delete_success}")

        # Step 6: Verify deletion
        workspace_exists_after = os.path.exists(test_file_path)
        container_exists_after = os.path.exists(container_file_path)
        print(f"📋 After deletion - Workspace: {workspace_exists_after}, Container: {container_exists_after}")

        # Step 7: Evaluate results
        workspace_deleted = workspace_exists and not workspace_exists_after
        container_deleted = container_exists and not container_exists_after

        print(f"\n📊 RESULTS:")
        print(f"  API deletion success: {delete_success}")
        print(f"  File deleted from workspace: {workspace_deleted}")
        print(f"  File deleted from container: {container_deleted}")

        if delete_success and workspace_deleted and container_deleted:
            print("🎉 SUCCESS: File deletion working with active container!")
            return True
        else:
            print("💥 FAILURE: File deletion has issues")
            return False

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup: stop container session
        try:
            print(f"🧹 Cleaning up container session...")
            await container_manager.stop_session(SESSION_UUID)
            print(f"✅ Container session stopped")
        except Exception as e:
            print(f"⚠️ Error stopping session: {e}")

async def main():
    """Main test function."""
    success = await test_with_container()
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())