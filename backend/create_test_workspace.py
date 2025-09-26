#!/usr/bin/env python3
"""Create a test workspace with files for integration testing."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.postgres_models import CodeSession, WorkspaceItem
from app.core.postgres import init_db

def create_test_workspace():
    """Create a test workspace session with files."""
    print("🔧 Creating test workspace for UI testing...")
    
    # Initialize database
    init_db()
    
    # Get test user (user_id=6 from logs)
    test_user_id = 6
    
    # Create a new session for testing
    session = CodeSession.create(
        user_id=test_user_id,
        name="UI Test Workspace",
        code='print("Hello from UI test workspace!")'
    )
    
    if not session:
        print("❌ Failed to create test session")
        return None
    
    print(f"✅ Created session: {session.uuid} (id: {session.id})")
    
    # Create test files
    main_file = WorkspaceItem.create(
        session_id=session.id,
        name="main.py",
        item_type="file",
        content='#!/usr/bin/env python3\nprint("Hello from main.py!")\nprint("This is a UI test file")'
    )
    
    utils_file = WorkspaceItem.create(
        session_id=session.id,
        name="utils.py",
        item_type="file", 
        content='def greet(name):\n    return f"Hello, {name}!"\n\ndef calculate(a, b):\n    return a + b'
    )
    
    config_file = WorkspaceItem.create(
        session_id=session.id,
        name="config.json",
        item_type="file",
        content='{\n  "app_name": "Test App",\n  "version": "1.0.0",\n  "debug": true\n}'
    )
    
    # Create a subdirectory with files
    tests_folder = WorkspaceItem.create(
        session_id=session.id,
        name="tests",
        item_type="folder"
    )
    
    test_file = WorkspaceItem.create(
        session_id=session.id,
        parent_id=tests_folder.id,
        name="test_main.py",
        item_type="file",
        content='import sys\nsys.path.append("..")\nfrom main import *\n\ndef test_main():\n    print("Test passed!")\n\nif __name__ == "__main__":\n    test_main()'
    )
    
    print(f"✅ Created workspace files:")
    print(f"   - main.py")
    print(f"   - utils.py")
    print(f"   - config.json")
    print(f"   - tests/")
    print(f"   - tests/test_main.py")
    print(f"")
    print(f"🔗 Session UUID: {session.uuid}")
    print(f"🆔 Session ID: {session.id}")
    
    return session.uuid

if __name__ == "__main__":
    session_uuid = create_test_workspace()
    if session_uuid:
        print(f"")
        print(f"✨ Test workspace created successfully!")
        print(f"   Use session UUID: {session_uuid}")
        print(f"   Open in UI to test workspace loading")
    else:
        print("❌ Failed to create test workspace")