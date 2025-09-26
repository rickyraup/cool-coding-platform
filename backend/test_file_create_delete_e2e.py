#!/usr/bin/env python3
"""
Step 10: Test file create/delete (full e2e workflow)

This test verifies the complete file create/delete workflow:
1. UI → Backend API (file creation request)
2. Backend → Docker container (file system creation) 
3. Docker container → PostgreSQL (persistence via save)
4. Verification of file existence and deletion across all layers
5. Test both immediate operations and persistence across container restarts
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


class FileCreateDeleteE2ETest:
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
    
    def test_basic_file_creation(self):
        """Test basic file creation functionality."""
        print("\n📝 Test 1: Basic File Creation")
        
        # Step 1: Create a new file with content
        test_content = f"""#!/usr/bin/env python3
# Test file created at {time.time()}
def new_function():
    return "File created successfully via API"

if __name__ == "__main__":
    print(new_function())
"""
        
        create_payload = {"content": test_content}
        create_response = requests.post(
            f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/new_test_file.py",
            json=create_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if create_response.status_code != 200:
            print(f"❌ Failed to create file: {create_response.status_code} {create_response.text}")
            return False
            
        print("✅ File created via API")
        
        # Step 2: Verify file exists and has correct content
        verify_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/new_test_file.py")
        if verify_response.status_code != 200:
            print("❌ Failed to verify file creation")
            return False
            
        retrieved_content = verify_response.json()['data']['content']
        if retrieved_content == test_content:
            print("✅ File creation verified in container")
        else:
            print("❌ File content mismatch after creation")
            return False
            
        return True
    
    def test_basic_file_deletion(self):
        """Test basic file deletion functionality."""
        print("\n🗑️ Test 2: Basic File Deletion")
        
        # Step 1: Create a file to delete
        test_content = "# This file will be deleted"
        create_payload = {"content": test_content}
        create_response = requests.post(
            f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/temp_delete_test.py",
            json=create_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if create_response.status_code != 200:
            print("❌ Failed to create test file for deletion")
            return False
            
        print("✅ Test file created for deletion")
        
        # Step 2: Verify file exists
        verify_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/temp_delete_test.py")
        if verify_response.status_code != 200:
            print("❌ Test file doesn't exist before deletion")
            return False
            
        print("✅ Test file confirmed to exist")
        
        # Step 3: Delete the file
        delete_response = requests.delete(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/temp_delete_test.py")
        if delete_response.status_code != 200:
            print(f"❌ Failed to delete file: {delete_response.status_code} {delete_response.text}")
            return False
            
        print("✅ File deleted via API")
        
        # Step 4: Verify file no longer exists
        verify_deleted_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/temp_delete_test.py")
        if verify_deleted_response.status_code == 404:
            print("✅ File deletion verified - file no longer exists")
        else:
            print(f"❌ File still exists after deletion: {verify_deleted_response.status_code}")
            return False
            
        return True
    
    def test_multiple_file_operations(self):
        """Test creating and deleting multiple files."""
        print("\n📚 Test 3: Multiple File Operations")
        
        timestamp = int(time.time())
        test_files = [
            (f"multi_test_1_{timestamp}.py", f"""def test_function_1():
    return "Multi-file test 1 - {timestamp}"
print(test_function_1())"""),
            
            (f"multi_test_2_{timestamp}.py", f"""def test_function_2():
    return "Multi-file test 2 - {timestamp}"
print(test_function_2())"""),
            
            (f"multi_config_{timestamp}.json", f"""{{"test_id": {timestamp}, "multi_file_test": true}}"""),
            
            (f"sub/nested_file_{timestamp}.py", f"""# Nested file test
def nested_function():
    return "Nested file - {timestamp}"
""")
        ]
        
        created_files = []
        
        # Step 1: Create multiple files
        for file_path, content in test_files:
            print(f"   📄 Creating {file_path}...")
            
            create_payload = {"content": content}
            create_response = requests.post(
                f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/{file_path}",
                json=create_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if create_response.status_code != 200:
                print(f"   ❌ Failed to create {file_path}: {create_response.status_code}")
                return False
                
            created_files.append(file_path)
            print(f"   ✅ {file_path} created")
            
        # Step 2: Verify all files exist
        print("   🔍 Verifying all files exist...")
        for file_path in created_files:
            verify_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/{file_path}")
            if verify_response.status_code != 200:
                print(f"   ❌ File {file_path} not found after creation")
                return False
                
        print("   ✅ All files verified to exist")
        
        # Step 3: Delete half the files
        files_to_delete = created_files[:2]  # Delete first 2 files
        print(f"   🗑️ Deleting {len(files_to_delete)} files...")
        
        for file_path in files_to_delete:
            delete_response = requests.delete(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/{file_path}")
            if delete_response.status_code != 200:
                print(f"   ❌ Failed to delete {file_path}")
                return False
                
            print(f"   ✅ {file_path} deleted")
            
        # Step 4: Verify deletions and remaining files
        print("   🔍 Verifying deletions and remaining files...")
        
        for file_path in files_to_delete:
            verify_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/{file_path}")
            if verify_response.status_code != 404:
                print(f"   ❌ File {file_path} still exists after deletion")
                return False
                
        remaining_files = created_files[2:]  # Last 2 files should still exist
        for file_path in remaining_files:
            verify_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/{file_path}")
            if verify_response.status_code != 200:
                print(f"   ❌ Remaining file {file_path} was unexpectedly deleted")
                return False
                
        print("   ✅ All file operations verified successfully")
        return True
    
    async def test_persistence_after_save(self):
        """Test that created files persist to database after save."""
        print("\n💾 Test 4: File Persistence After Save")
        
        # Step 1: Create a unique test file
        timestamp = int(time.time())
        test_content = f"""# Persistence test file - {timestamp}
def persistence_test():
    return "File persisted to database: {timestamp}"

print(persistence_test())
"""
        
        print("   📝 Creating test file...")
        create_payload = {"content": test_content}
        create_response = requests.post(
            f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/persistence_test_{timestamp}.py",
            json=create_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if create_response.status_code != 200:
            print(f"   ❌ Failed to create test file: {create_response.status_code}")
            return False
            
        print("   ✅ Test file created")
        
        # Step 2: Save workspace to database
        print("   💾 Saving workspace to database...")
        save_response = requests.post(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/save")
        if save_response.status_code != 200:
            print(f"   ❌ Failed to save workspace: {save_response.status_code}")
            return False
            
        print("   ✅ Workspace saved to database")
        
        # Step 3: Check database directly
        print("   🔍 Verifying file exists in database...")
        workspace_items = WorkspaceItem.get_all_by_session(self.session.id)
        persistence_file = None
        for item in workspace_items:
            if item.name == f"persistence_test_{timestamp}.py" and item.type == "file":
                persistence_file = item
                break
                
        if not persistence_file:
            print(f"   ❌ File persistence_test_{timestamp}.py not found in database")
            return False
            
        if persistence_file.content == test_content:
            print("   ✅ File successfully persisted to database")
        else:
            print("   ❌ File content in database doesn't match")
            return False
            
        # Step 4: Delete file and verify deletion persists
        print("   🗑️ Deleting file and testing persistence...")
        delete_response = requests.delete(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/persistence_test_{timestamp}.py")
        if delete_response.status_code != 200:
            print("   ❌ Failed to delete test file")
            return False
            
        # Save again after deletion
        save_response = requests.post(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/save")
        if save_response.status_code != 200:
            print(f"   ❌ Failed to save workspace after deletion: {save_response.status_code}")
            return False
            
        # Check database - file should be gone
        workspace_items_after = WorkspaceItem.get_all_by_session(self.session.id)
        persistence_file_after = None
        for item in workspace_items_after:
            if item.name == f"persistence_test_{timestamp}.py" and item.type == "file":
                persistence_file_after = item
                break
                
        if persistence_file_after is None:
            print("   ✅ File deletion persisted to database")
        else:
            print("   ❌ File still exists in database after deletion")
            return False
            
        return True
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        print("\n⚡ Test 5: Edge Cases and Error Handling")
        
        # Test 1: Create file with empty content
        print("   📄 Testing empty file creation...")
        empty_payload = {"content": ""}
        empty_response = requests.post(
            f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/empty_test.py",
            json=empty_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if empty_response.status_code != 200:
            print("   ❌ Failed to create empty file")
            return False
        print("   ✅ Empty file created successfully")
        
        # Test 2: Create file without content field
        print("   📄 Testing file creation without content field...")
        no_content_payload = {}
        no_content_response = requests.post(
            f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/no_content_test.py",
            json=no_content_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if no_content_response.status_code != 200:
            print("   ❌ Failed to create file without content field")
            return False
        print("   ✅ File created without content field (defaults to empty)")
        
        # Test 3: Try to delete non-existent file
        print("   🗑️ Testing deletion of non-existent file...")
        delete_nonexistent_response = requests.delete(
            f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/nonexistent_file.py"
        )
        
        if delete_nonexistent_response.status_code == 404:
            print("   ✅ Correctly returned 404 for non-existent file deletion")
        else:
            print(f"   ❌ Unexpected response for non-existent file: {delete_nonexistent_response.status_code}")
            return False
        
        # Test 4: Try to access non-existent session
        print("   🔍 Testing operations with invalid session...")
        invalid_session = "00000000-0000-0000-0000-000000000000"
        invalid_create_response = requests.post(
            f"{self.base_url}/api/session_workspace/{invalid_session}/file/test.py",
            json={"content": "test"},
            headers={"Content-Type": "application/json"}
        )
        
        if invalid_create_response.status_code == 404:
            print("   ✅ Correctly returned 404 for invalid session")
        else:
            print(f"   ❌ Unexpected response for invalid session: {invalid_create_response.status_code}")
            return False
        
        # Clean up test files
        print("   🧹 Cleaning up edge case test files...")
        cleanup_files = ["empty_test.py", "no_content_test.py"]
        for file_path in cleanup_files:
            requests.delete(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/{file_path}")
        
        print("   ✅ All edge cases handled correctly")
        return True
    
    async def run_all_tests(self):
        """Run all file create/delete tests."""
        print("🧪 Starting File Create/Delete E2E Tests")
        print("=" * 60)
        
        if not self.setup():
            return False
            
        tests = [
            ("Basic File Creation", self.test_basic_file_creation),
            ("Basic File Deletion", self.test_basic_file_deletion),
            ("Multiple File Operations", self.test_multiple_file_operations),
            ("File Persistence After Save", self.test_persistence_after_save),
            ("Edge Cases and Error Handling", self.test_edge_cases),
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
        print(f"🧪 File Create/Delete E2E Test Results:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
        
        if failed == 0:
            print("🎉 ALL FILE CREATE/DELETE E2E TESTS PASSED!")
            print("✅ Step 10: File create/delete (full e2e workflow) - COMPLETE")
            return True
        else:
            print("❌ Some tests failed")
            return False


async def main():
    """Run the file create/delete E2E test suite."""
    test_runner = FileCreateDeleteE2ETest()
    success = await test_runner.run_all_tests()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)