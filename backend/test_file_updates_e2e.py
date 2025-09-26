#!/usr/bin/env python3
"""
Step 8: Test file updates (full e2e workflow)

This test verifies the complete file update workflow:
1. UI → Backend API (file update request)
2. Backend → Docker container (file system update) 
3. Docker container → PostgreSQL (persistence)
4. Verification of consistency across all layers
5. Test both immediate updates and persistence across container restarts
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import time
from app.models.postgres_models import CodeSession, WorkspaceItem
from app.core.postgres import init_db
from app.services.container_manager import container_manager
from app.services.workspace_loader import workspace_loader


class FileUpdateE2ETest:
    def __init__(self):
        self.base_url = "http://localhost:8002"
        self.test_session_uuid = "19d05e0c-205d-4414-9acc-a092c9135444"
        self.session = None
        
    def setup(self):
        """Initialize test environment."""
        print("🔧 Setting up test environment...")
        
        # Initialize database
        init_db()
        
        # Get test session
        self.session = CodeSession.get_by_uuid(self.test_session_uuid)
        if not self.session:
            print(f"❌ Test session {self.test_session_uuid} not found")
            return False
            
        print(f"✅ Test session found: {self.session.name} (id: {self.session.id})")
        
        # Ensure container session is running
        start_response = requests.post(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/container/start")
        if start_response.status_code != 200:
            print(f"❌ Failed to start container: {start_response.status_code}")
            return False
            
        print("✅ Container session started")
        return True
    
    def test_basic_file_update(self):
        """Test basic file update functionality."""
        print("\n📝 Test 1: Basic File Update")
        
        # Step 1: Get original file content
        original_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/main.py")
        if original_response.status_code != 200:
            print("❌ Failed to get original file content")
            return False
            
        original_content = original_response.json()['data']['content']
        print(f"✅ Original content retrieved ({len(original_content)} chars)")
        
        # Step 2: Update file with new content
        new_content = f"""#!/usr/bin/env python3
# Updated at {time.time()}
print("File update test - Step 1")
print("This file was updated via API")

def test_function():
    return "API update successful"

if __name__ == "__main__":
    print(test_function())
"""
        
        update_payload = {"content": new_content}
        update_response = requests.put(
            f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/main.py",
            json=update_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if update_response.status_code != 200:
            print(f"❌ Failed to update file: {update_response.status_code} {update_response.text}")
            return False
            
        print("✅ File updated via API")
        
        # Step 3: Verify update in container
        verify_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/main.py")
        if verify_response.status_code != 200:
            print("❌ Failed to verify file update")
            return False
            
        updated_content = verify_response.json()['data']['content']
        if updated_content == new_content:
            print("✅ File update verified in container")
        else:
            print("❌ File content mismatch after update")
            return False
            
        return True
    
    def test_multiple_file_updates(self):
        """Test updating multiple files in sequence."""
        print("\n📚 Test 2: Multiple File Updates")
        
        timestamp = time.time()
        test_files = [
            ("utils.py", f"""def updated_greet(name):
    return f"Hello, {{name}}! (Updated via API)"

def calculate_advanced(a, b, operation="add"):
    if operation == "add":
        return a + b
    elif operation == "multiply":
        return a * b
    return 0

# Test update timestamp: {timestamp}"""),
            
            ("config.json", f"""{{
  "app_name": "Test App Updated",
  "version": "2.0.0",
  "debug": false,
  "updated_via_api": true,
  "timestamp": {int(time.time())}
}}"""),
            
            ("tests/test_main.py", """import sys
sys.path.append("..")
from main import *

def test_main_updated():
    print("Updated test - API integration working!")
    return True

def test_api_functionality():
    # Test added via API update
    assert test_main_updated() == True
    print("All tests passed!")

if __name__ == "__main__":
    test_api_functionality()
""")
        ]
        
        for file_path, content in test_files:
            print(f"   📄 Updating {file_path}...")
            
            update_payload = {"content": content}
            update_response = requests.put(
                f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/{file_path}",
                json=update_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if update_response.status_code != 200:
                print(f"   ❌ Failed to update {file_path}: {update_response.status_code}")
                return False
                
            # Verify update
            verify_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/{file_path}")
            if verify_response.status_code != 200:
                print(f"   ❌ Failed to verify {file_path}")
                return False
                
            updated_content = verify_response.json()['data']['content']
            if updated_content == content:
                print(f"   ✅ {file_path} updated and verified")
            else:
                print(f"   ❌ {file_path} content mismatch")
                return False
                
        return True
    
    async def test_persistence_across_container_restart(self):
        """Test that file updates persist across container restarts."""
        print("\n🔄 Test 3: Persistence Across Container Restart")
        
        # Step 1: Create a unique test file with timestamp
        timestamp = int(time.time())
        test_content = f"""# Persistence test file
# Created at timestamp: {timestamp}

def persistence_test():
    return "File persisted across container restart: {timestamp}"

print("Testing persistence...")
print(persistence_test())
"""
        
        print("   📝 Creating test file...")
        update_payload = {"content": test_content}
        update_response = requests.put(
            f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/persistence_test.py",
            json=update_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if update_response.status_code != 200:
            print(f"   ❌ Failed to create test file: {update_response.status_code}")
            return False
            
        print("   ✅ Test file created")
        
        # Step 2: Force container cleanup and restart
        print("   🐳 Cleaning up container...")
        session_str = str(self.session.id)
        if session_str in container_manager.active_sessions:
            await container_manager.cleanup_session(session_str)
            
        # Wait a moment for cleanup
        await asyncio.sleep(2)
        
        # Step 3: Restart container and load workspace
        print("   🚀 Restarting container...")
        start_response = requests.post(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/container/start")
        if start_response.status_code != 200:
            print(f"   ❌ Failed to restart container: {start_response.status_code}")
            return False
            
        # Step 4: Verify file still exists with correct content
        print("   🔍 Verifying file persistence...")
        verify_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/persistence_test.py")
        if verify_response.status_code != 200:
            print("   ❌ File not found after restart")
            return False
            
        retrieved_content = verify_response.json()['data']['content']
        if retrieved_content == test_content:
            print("   ✅ File persisted across container restart")
        else:
            print("   ❌ File content changed after restart")
            print(f"   Expected: {test_content[:50]}...")
            print(f"   Got: {retrieved_content[:50]}...")
            return False
            
        return True
    
    def test_database_synchronization(self):
        """Test that database stays synchronized with file updates."""
        print("\n💾 Test 4: Database Synchronization")
        
        # Step 1: Update a file via API
        test_content = f"""# Database sync test
# Updated at: {time.time()}

def db_sync_test():
    return "Database synchronization working"
"""
        
        print("   📝 Updating file via API...")
        update_payload = {"content": test_content}
        update_response = requests.put(
            f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/utils.py",
            json=update_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if update_response.status_code != 200:
            print(f"   ❌ Failed to update file: {update_response.status_code}")
            return False
            
        print("   ✅ File updated via API")
        
        # Step 2: Save workspace to database
        print("   💾 Saving workspace to database...")
        save_response = requests.post(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/save")
        if save_response.status_code != 200:
            print(f"   ❌ Failed to save workspace: {save_response.status_code}")
            return False
            
        print("   ✅ Workspace saved to database")
        
        # Step 3: Check database directly
        print("   🔍 Verifying database content...")
        workspace_items = WorkspaceItem.get_all_by_session(self.session.id)
        utils_item = None
        for item in workspace_items:
            if item.name == "utils.py" and item.type == "file":
                utils_item = item
                break
                
        if not utils_item:
            print("   ❌ utils.py not found in database")
            return False
            
        if utils_item.content == test_content:
            print("   ✅ Database content matches file update")
        else:
            print("   ❌ Database content doesn't match")
            return False
            
        return True
    
    def test_concurrent_updates(self):
        """Test handling of rapid sequential updates."""
        print("\n⚡ Test 5: Rapid Sequential Updates")
        
        base_content = """# Rapid update test file
# Update number: {}

def rapid_update_test(update_num):
    return f"Update #{{update_num}} completed successfully"

print(rapid_update_test({}))
"""
        
        # Perform 5 rapid updates
        for i in range(1, 6):
            content = base_content.format(i, i)
            
            print(f"   📝 Update #{i}...")
            update_payload = {"content": content}
            update_response = requests.put(
                f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/rapid_test.py",
                json=update_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if update_response.status_code != 200:
                print(f"   ❌ Update #{i} failed: {update_response.status_code}")
                return False
                
            # Brief pause between updates
            time.sleep(0.1)
            
        # Verify final state
        print("   🔍 Verifying final state...")
        verify_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/rapid_test.py")
        if verify_response.status_code != 200:
            print("   ❌ Failed to verify final state")
            return False
            
        final_content = verify_response.json()['data']['content']
        expected_final = base_content.format(5, 5)
        
        if final_content == expected_final:
            print("   ✅ All rapid updates completed successfully")
        else:
            print("   ❌ Final content doesn't match expected")
            return False
            
        return True
    
    async def run_all_tests(self):
        """Run all file update tests."""
        print("🧪 Starting File Update E2E Tests")
        print("=" * 60)
        
        if not self.setup():
            return False
            
        tests = [
            ("Basic File Update", self.test_basic_file_update),
            ("Multiple File Updates", self.test_multiple_file_updates),
            ("Persistence Across Restart", self.test_persistence_across_container_restart),
            ("Database Synchronization", self.test_database_synchronization),
            ("Rapid Sequential Updates", self.test_concurrent_updates),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                    
                if result:
                    print(f"✅ {test_name} - PASSED")
                    passed += 1
                else:
                    print(f"❌ {test_name} - FAILED")
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name} - ERROR: {e}")
                failed += 1
                
        print("\n" + "=" * 60)
        print(f"🧪 File Update E2E Test Results:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
        
        if failed == 0:
            print("🎉 ALL FILE UPDATE E2E TESTS PASSED!")
            print("✅ Step 8: File updates (full e2e workflow) - COMPLETE")
            return True
        else:
            print("❌ Some tests failed")
            return False


async def main():
    """Run the file update E2E test suite."""
    test_runner = FileUpdateE2ETest()
    success = await test_runner.run_all_tests()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)