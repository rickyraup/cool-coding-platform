#!/usr/bin/env python3
"""Integration test for workspace file loading: PostgreSQL → Docker container → UI"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.postgres_models import CodeSession, WorkspaceItem
from app.services.workspace_loader import workspace_loader
from app.services.container_manager import container_manager


async def test_workspace_loading_integration():
    """Test the complete workspace loading workflow."""
    print("🧪 Starting workspace loading integration test...")
    
    # Step 1: Create a test session with workspace items
    print("\n📋 Step 1: Creating test session with workspace items")
    
    # First, get a test user (assuming user_id=6 from logs)
    test_user_id = 6
    
    # Create a new session for testing
    session = CodeSession.create(
        user_id=test_user_id,
        name="Integration Test Session",
        code='print("Hello from test session")'
    )
    
    if not session:
        print("❌ Failed to create test session")
        return False
    
    print(f"✅ Created session: {session.uuid} (id: {session.id})")
    
    # Step 2: Add workspace items to the session
    print("\n📁 Step 2: Adding workspace items to session")
    
    # Create test files
    main_file = WorkspaceItem.create(
        session_id=session.id,
        name="main.py",
        item_type="file",
        content='print("Hello, World!")\nprint("Integration test file")'
    )
    
    utils_file = WorkspaceItem.create(
        session_id=session.id,
        name="utils.py", 
        item_type="file",
        content='def hello():\n    return "Hello from utils!"'
    )
    
    # Create a folder and nested file
    folder = WorkspaceItem.create(
        session_id=session.id,
        name="tests",
        item_type="folder"
    )
    
    nested_file = WorkspaceItem.create(
        session_id=session.id,
        parent_id=folder.id,
        name="test_main.py",
        item_type="file", 
        content='import sys\nsys.path.append("..")\nfrom main import *\nprint("Test passed!")'
    )
    
    print(f"✅ Created workspace items: main.py, utils.py, tests/, tests/test_main.py")
    
    # Step 3: Test workspace loading into container
    print(f"\n🐳 Step 3: Loading workspace into container (session_id: {session.id})")
    
    # Load workspace into container
    success = await workspace_loader.load_workspace_into_container(session.id)
    
    if not success:
        print("❌ Failed to load workspace into container")
        return False
    
    print("✅ Workspace loaded into container successfully")
    
    # Step 4: Verify files exist in container
    print("\n🔍 Step 4: Verifying files exist in container")
    
    # Find the container session
    session_str = str(session.id)
    active_session_id = container_manager.find_session_by_workspace_id(session_str)
    
    if not active_session_id:
        # Try to create container session
        container_session = await container_manager.get_or_create_session(session_str)
        working_dir = container_session.working_dir
        active_session_id = session_str
    else:
        container_session = container_manager.active_sessions[active_session_id]
        working_dir = container_session.working_dir
    
    print(f"✅ Container session active: {active_session_id}")
    print(f"✅ Working directory: {working_dir}")
    
    # Check if files exist in container
    import os
    main_py_path = os.path.join(working_dir, "main.py")
    utils_py_path = os.path.join(working_dir, "utils.py")
    tests_dir_path = os.path.join(working_dir, "tests")
    test_file_path = os.path.join(working_dir, "tests", "test_main.py")
    
    files_exist = []
    for path, name in [(main_py_path, "main.py"), (utils_py_path, "utils.py"), (tests_dir_path, "tests/"), (test_file_path, "tests/test_main.py")]:
        exists = os.path.exists(path)
        files_exist.append(exists)
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {'exists' if exists else 'missing'}")
    
    if not all(files_exist):
        print("❌ Some files are missing in container")
        return False
    
    # Step 5: Test file content
    print("\n📖 Step 5: Verifying file contents")
    
    with open(main_py_path, 'r') as f:
        main_content = f.read()
        expected = 'print("Hello, World!")\nprint("Integration test file")'
        if main_content == expected:
            print("✅ main.py content matches")
        else:
            print(f"❌ main.py content mismatch:\nExpected: {expected}\nActual: {main_content}")
            return False
    
    # Step 6: Test workspace file operations via API
    print("\n🔗 Step 6: Testing workspace file operations via workspace_loader")
    
    # Test get file content
    retrieved_content = await workspace_loader.get_workspace_file_content(session.id, "main.py")
    if retrieved_content == expected:
        print("✅ get_workspace_file_content works")
    else:
        print(f"❌ get_workspace_file_content failed: {retrieved_content}")
        return False
    
    # Test update file content  
    new_content = 'print("Updated content!")\nprint("Integration test passed!")'
    update_success = await workspace_loader.update_workspace_file_content(session.id, "main.py", new_content)
    if update_success:
        print("✅ update_workspace_file_content works")
    else:
        print("❌ update_workspace_file_content failed")
        return False
    
    # Verify update worked
    updated_content = await workspace_loader.get_workspace_file_content(session.id, "main.py")
    if updated_content == new_content:
        print("✅ File content update verified")
    else:
        print(f"❌ File content not updated correctly: {updated_content}")
        return False
    
    print("\n🎉 All integration tests passed!")
    
    # Cleanup
    print("\n🧹 Cleanup: Removing test session")
    session.delete()
    
    # Cleanup container
    if active_session_id in container_manager.active_sessions:
        await container_manager.cleanup_session(active_session_id)
        print("✅ Container cleaned up")
    
    return True


if __name__ == "__main__":
    # Initialize database first
    from app.core.postgres import init_db
    init_db()
    
    result = asyncio.run(test_workspace_loading_integration())
    sys.exit(0 if result else 1)