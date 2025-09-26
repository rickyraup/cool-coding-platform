#!/usr/bin/env python3
"""
Integration test for Step 6: Test file fetching (backend integration + UI)

This test verifies the complete file fetching workflow:
1. PostgreSQL → Docker container (workspace loading) 
2. Docker container → UI (file fetching)
3. API endpoints work correctly
4. Frontend can retrieve workspace tree and file contents
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from app.models.postgres_models import CodeSession, WorkspaceItem
from app.core.postgres import init_db
from app.services.container_manager import container_manager
from app.services.workspace_loader import workspace_loader


def test_api_endpoints():
    """Test all the file fetching API endpoints via HTTP requests."""
    print("🧪 Testing file fetching API endpoints...")
    
    # Use our test session UUID
    test_session_uuid = "19d05e0c-205d-4414-9acc-a092c9135444"
    base_url = "http://localhost:8002"
    
    # Test 1: Start container session and load workspace
    print(f"\n📋 Step 1: Starting container session for {test_session_uuid}")
    
    start_response = requests.post(f"{base_url}/api/session_workspace/{test_session_uuid}/container/start")
    if start_response.status_code != 200:
        print(f"❌ Failed to start container session: {start_response.status_code} {start_response.text}")
        return False
    
    start_data = start_response.json()
    print(f"✅ Container session started: {start_data['message']}")
    
    # Test 2: Get workspace tree structure
    print(f"\n🌳 Step 2: Getting workspace tree structure")
    
    tree_response = requests.get(f"{base_url}/api/session_workspace/{test_session_uuid}/workspace/tree")
    if tree_response.status_code != 200:
        print(f"❌ Failed to get workspace tree: {tree_response.status_code} {tree_response.text}")
        return False
    
    tree_data = tree_response.json()
    print(f"✅ Workspace tree retrieved: {len(tree_data['data'])} items found")
    
    # Print the tree structure for verification
    for item in tree_data['data']:
        if item['type'] == 'folder':
            print(f"   📁 {item['name']} ({item['full_path']})")
            if item.get('children'):
                for child in item['children']:
                    print(f"      📄 {child['name']} ({child['full_path']})")
        else:
            print(f"   📄 {item['name']} ({item['full_path']})")
    
    # Test 3: Fetch individual file contents
    print(f"\n📖 Step 3: Fetching file contents")
    
    test_files = [
        "main.py",
        "utils.py", 
        "config.json",
        "tests/test_main.py"
    ]
    
    for file_path in test_files:
        print(f"   🔍 Fetching {file_path}...")
        file_response = requests.get(f"{base_url}/api/session_workspace/{test_session_uuid}/file/{file_path}")
        
        if file_response.status_code == 200:
            file_data = file_response.json()
            content = file_data['data']['content']
            print(f"   ✅ {file_path} ({len(content)} chars)")
            # Print first line of content as preview
            first_line = content.split('\n')[0] if content else '(empty)'
            print(f"      Preview: {first_line}")
        else:
            print(f"   ❌ Failed to fetch {file_path}: {file_response.status_code}")
            return False
    
    # Test 4: Test file update functionality
    print(f"\n✏️  Step 4: Testing file update")
    
    update_content = 'print("Updated via API test!")\nprint("File fetching integration works!")'
    update_payload = {"content": update_content}
    
    update_response = requests.put(
        f"{base_url}/api/session_workspace/{test_session_uuid}/file/main.py",
        json=update_payload,
        headers={"Content-Type": "application/json"}
    )
    
    if update_response.status_code != 200:
        print(f"❌ Failed to update file: {update_response.status_code} {update_response.text}")
        return False
    
    print("✅ File updated successfully")
    
    # Verify the update by fetching the file again
    verify_response = requests.get(f"{base_url}/api/session_workspace/{test_session_uuid}/file/main.py")
    if verify_response.status_code == 200:
        verify_data = verify_response.json()
        if verify_data['data']['content'] == update_content:
            print("✅ File update verified - content matches")
        else:
            print(f"❌ File update verification failed - content mismatch")
            return False
    else:
        print(f"❌ Failed to verify file update: {verify_response.status_code}")
        return False
    
    print(f"\n🎉 All file fetching API tests passed!")
    return True


async def test_backend_integration():
    """Test the backend integration components directly."""
    print("\n🔧 Testing backend integration components...")
    
    # Test 1: Session and workspace items exist in database
    print("📋 Step 1: Verifying database state")
    
    session = CodeSession.get_by_uuid("19d05e0c-205d-4414-9acc-a092c9135444")
    if not session:
        print("❌ Test session not found in database")
        return False
    
    print(f"✅ Session found: {session.name} (id: {session.id})")
    
    workspace_items = WorkspaceItem.get_all_by_session(session.id)
    print(f"✅ {len(workspace_items)} workspace items found in database")
    
    # Test 2: Container session management
    print("\n🐳 Step 2: Testing container session management")
    
    session_str = str(session.id)
    container_session = await container_manager.get_or_create_session(session_str)
    print(f"✅ Container session active: {container_session.container_id}")
    print(f"✅ Working directory: {container_session.working_dir}")
    
    # Test 3: Workspace loader functionality
    print("\n📁 Step 3: Testing workspace loader")
    
    # Test file content retrieval
    main_content = await workspace_loader.get_workspace_file_content(session.id, "main.py")
    if main_content:
        print(f"✅ File content retrieved: main.py ({len(main_content)} chars)")
    else:
        print("❌ Failed to retrieve file content")
        return False
    
    # Test file content update
    test_content = 'print("Backend integration test!")'
    update_success = await workspace_loader.update_workspace_file_content(
        session.id, "utils.py", test_content
    )
    if update_success:
        print("✅ File content updated successfully")
    else:
        print("❌ Failed to update file content")
        return False
    
    # Verify update
    updated_content = await workspace_loader.get_workspace_file_content(session.id, "utils.py")
    if updated_content == test_content:
        print("✅ File update verified")
    else:
        print("❌ File update verification failed")
        return False
    
    print(f"\n🎉 All backend integration tests passed!")
    return True


def main():
    """Run the complete file fetching integration test."""
    print("🧪 Starting File Fetching Integration Test")
    print("=" * 60)
    
    # Initialize database
    print("🗄️ Initializing database...")
    init_db()
    
    # Test API endpoints (simulates frontend calls)
    api_success = test_api_endpoints()
    
    if not api_success:
        print("❌ API endpoint tests failed")
        return False
    
    # Test backend integration components
    backend_success = asyncio.run(test_backend_integration())
    
    if not backend_success:
        print("❌ Backend integration tests failed")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL FILE FETCHING INTEGRATION TESTS PASSED!")
    print("✅ Step 6: File fetching (Docker container → UI) - COMPLETE")
    print("✅ API endpoints working correctly")
    print("✅ Frontend can retrieve workspace tree and file contents")
    print("✅ File updates work end-to-end")
    print("✅ Backend integration components functioning properly")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)