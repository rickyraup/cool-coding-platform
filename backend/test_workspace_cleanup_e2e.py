#!/usr/bin/env python3
"""
Step 11: Test workspace cleanup (Docker container destruction)

This test verifies the complete workspace cleanup workflow:
1. Create active container session
2. Verify container is running and functional  
3. Test manual cleanup via API
4. Test automatic cleanup triggers (idle timeout, resource limits)
5. Verify complete cleanup (container stopped, workspace saved, resources freed)
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


class WorkspaceCleanupE2ETest:
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
        return True
    
    def test_manual_cleanup_api(self):
        """Test manual workspace cleanup via API."""
        print("\n🧹 Test 1: Manual Cleanup via API")
        
        # Step 1: Start container session
        print("   🚀 Starting container session...")
        start_response = requests.post(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/container/start")
        if start_response.status_code != 200:
            print(f"   ❌ Failed to start container: {start_response.status_code}")
            return False
        print("   ✅ Container session started")
        
        # Step 2: Verify container is active
        print("   🔍 Verifying container is active...")
        status_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/container/status")
        if status_response.status_code != 200:
            print("   ❌ Failed to get container status")
            return False
            
        status_data = status_response.json()['data']
        if not status_data['container_active']:
            print("   ❌ Container is not active")
            return False
        print(f"   ✅ Container is active: {status_data['container_id']}")
        
        # Step 3: Create some test content to verify workspace persistence
        print("   📄 Creating test content...")
        test_content = f"# Cleanup test file created at {time.time()}\nprint('Cleanup test successful!')"
        create_payload = {"content": test_content}
        create_response = requests.post(
            f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/file/cleanup_test.py",
            json=create_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if create_response.status_code != 200:
            print("   ❌ Failed to create test content")
            return False
        print("   ✅ Test content created")
        
        # Step 4: Manual cleanup via API
        print("   🧹 Triggering manual cleanup...")
        cleanup_response = requests.post(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/container/cleanup")
        if cleanup_response.status_code != 200:
            print(f"   ❌ Cleanup failed: {cleanup_response.status_code} {cleanup_response.text}")
            return False
        print("   ✅ Manual cleanup completed successfully")
        
        # Step 5: Verify container is no longer active
        print("   🔍 Verifying container cleanup...")
        verify_response = requests.get(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/container/status")
        if verify_response.status_code != 200:
            print("   ❌ Failed to verify container status")
            return False
            
        verify_data = verify_response.json()['data']
        if verify_data['container_active']:
            print("   ❌ Container is still active after cleanup")
            return False
        print("   ✅ Container successfully cleaned up")
        
        # Step 6: Verify workspace was saved to database
        print("   💾 Verifying workspace persistence...")
        workspace_items = WorkspaceItem.get_all_by_session(self.session.id)
        cleanup_file = None
        for item in workspace_items:
            if item.name == "cleanup_test.py" and item.type == "file":
                cleanup_file = item
                break
                
        if not cleanup_file:
            print("   ❌ Test file not found in database after cleanup")
            return False
            
        if cleanup_file.content == test_content:
            print("   ✅ Workspace was properly saved to database during cleanup")
        else:
            print("   ❌ Workspace content mismatch in database")
            return False
        
        return True
    
    async def test_automatic_resource_cleanup(self):
        """Test automatic cleanup due to resource limits."""
        print("\n⚡ Test 2: Automatic Resource-based Cleanup")
        
        # Get current resource limits
        print("   📊 Getting current resource limits...")
        original_max_containers = container_manager.max_total_containers
        original_max_per_user = container_manager.max_containers_per_user
        
        print(f"   📋 Current limits: {original_max_containers} total, {original_max_per_user} per user")
        
        # Temporarily lower limits for testing
        container_manager.max_total_containers = 2
        container_manager.max_containers_per_user = 1
        
        try:
            # Step 1: Start first container session
            print("   🚀 Starting first container session...")
            start_response_1 = requests.post(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/container/start")
            if start_response_1.status_code != 200:
                print("   ❌ Failed to start first container")
                return False
            print("   ✅ First container session started")
            
            # Step 2: Get session info to verify it's active
            session_info_1 = await container_manager.get_session_info(str(self.session.id))
            if not session_info_1:
                print("   ❌ First session not found in container manager")
                return False
            print(f"   ✅ First session verified: {session_info_1['container_id']}")
            
            # Step 3: Create a second session that should trigger cleanup
            print("   🚀 Creating second session to trigger resource limit...")
            
            # Create another session (this will exceed the limit we set)
            second_session_id = "test_cleanup_session_" + str(int(time.time()))
            second_session = await container_manager.create_session(second_session_id)
            if not second_session:
                print("   ❌ Failed to create second session")
                return False
            print(f"   ✅ Second session created: {second_session.container_id}")
            
            # Step 4: Verify resource limit enforcement cleaned up old session
            await asyncio.sleep(2)  # Give cleanup time to process
            
            session_info_after = await container_manager.get_session_info(str(self.session.id))
            if session_info_after:
                print("   ❌ First session was not cleaned up by resource limits")
                # Clean up manually
                await container_manager.cleanup_session(str(self.session.id))
                await container_manager.cleanup_session(second_session_id)
                return False
                
            print("   ✅ Resource limit cleanup worked - old session was removed")
            
            # Clean up the second session
            await container_manager.cleanup_session(second_session_id)
            print("   ✅ Second session cleaned up")
            
            return True
            
        finally:
            # Restore original limits
            container_manager.max_total_containers = original_max_containers
            container_manager.max_containers_per_user = original_max_per_user
            print(f"   🔄 Restored original limits: {original_max_containers} total, {original_max_per_user} per user")
    
    async def test_idle_timeout_cleanup(self):
        """Test automatic cleanup due to idle timeout."""
        print("\n⏰ Test 3: Automatic Idle Timeout Cleanup")
        
        # Get current idle timeout
        original_timeout = container_manager.idle_timeout_minutes
        
        # Set very short timeout for testing (1 minute -> 0.1 minute = 6 seconds)
        container_manager.idle_timeout_minutes = 0.1
        
        try:
            print(f"   ⏱️ Set timeout to {container_manager.idle_timeout_minutes} minutes for testing")
            
            # Step 1: Start container session
            print("   🚀 Starting container session...")
            start_response = requests.post(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/container/start")
            if start_response.status_code != 200:
                print("   ❌ Failed to start container")
                return False
            print("   ✅ Container session started")
            
            # Step 2: Verify it's active
            session_info = await container_manager.get_session_info(str(self.session.id))
            if not session_info:
                print("   ❌ Session not found in container manager")
                return False
            print(f"   ✅ Session active: {session_info['container_id']}")
            
            # Step 3: Wait for idle timeout to trigger
            print("   ⏳ Waiting for idle timeout (10 seconds)...")
            await asyncio.sleep(10)
            
            # Step 4: Trigger idle cleanup manually (simulating background task)
            print("   🧹 Running idle cleanup check...")
            cleanup_count = await container_manager.cleanup_idle_sessions()
            if cleanup_count == 0:
                print("   ❌ Idle cleanup did not remove any sessions")
                # Clean up manually
                await container_manager.cleanup_session(str(self.session.id))
                return False
                
            print(f"   ✅ Idle cleanup removed {cleanup_count} sessions")
            
            # Step 5: Verify session was cleaned up
            session_info_after = await container_manager.get_session_info(str(self.session.id))
            if session_info_after:
                print("   ❌ Session was not cleaned up by idle timeout")
                await container_manager.cleanup_session(str(self.session.id))
                return False
                
            print("   ✅ Idle timeout cleanup worked successfully")
            return True
            
        finally:
            # Restore original timeout
            container_manager.idle_timeout_minutes = original_timeout
            print(f"   🔄 Restored original timeout: {original_timeout} minutes")
    
    def test_cleanup_endpoint_edge_cases(self):
        """Test cleanup endpoint edge cases."""
        print("\n🔍 Test 4: Cleanup Endpoint Edge Cases")
        
        # Test 1: Cleanup non-existent session
        print("   🧹 Testing cleanup of non-existent session...")
        invalid_uuid = "00000000-0000-0000-0000-000000000000"
        cleanup_response = requests.post(f"{self.base_url}/api/session_workspace/{invalid_uuid}/container/cleanup")
        
        if cleanup_response.status_code == 404:
            print("   ✅ Correctly returned 404 for non-existent session")
        else:
            print(f"   ❌ Unexpected response for non-existent session: {cleanup_response.status_code}")
            return False
        
        # Test 2: Cleanup session with no active container
        print("   🧹 Testing cleanup of session with no active container...")
        cleanup_response = requests.post(f"{self.base_url}/api/session_workspace/{self.test_session_uuid}/container/cleanup")
        
        if cleanup_response.status_code == 200:
            response_data = cleanup_response.json()
            if "No active container session" in response_data.get("message", ""):
                print("   ✅ Correctly handled cleanup of inactive container")
            else:
                print("   ❌ Unexpected message for inactive container cleanup")
                return False
        else:
            print(f"   ❌ Unexpected response for inactive container cleanup: {cleanup_response.status_code}")
            return False
        
        print("   ✅ All edge cases handled correctly")
        return True
    
    async def run_all_tests(self):
        """Run all workspace cleanup tests."""
        print("🧪 Starting Workspace Cleanup E2E Tests")
        print("=" * 60)
        
        if not self.setup():
            return False
            
        tests = [
            ("Manual Cleanup via API", self.test_manual_cleanup_api),
            ("Automatic Resource-based Cleanup", self.test_automatic_resource_cleanup),
            ("Automatic Idle Timeout Cleanup", self.test_idle_timeout_cleanup),
            ("Cleanup Endpoint Edge Cases", self.test_cleanup_endpoint_edge_cases),
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
        print(f"🧪 Workspace Cleanup E2E Test Results:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
        
        if failed == 0:
            print("🎉 ALL WORKSPACE CLEANUP E2E TESTS PASSED!")
            print("✅ Step 11: Workspace cleanup (Docker container destruction) - COMPLETE")
            return True
        else:
            print("❌ Some tests failed")
            return False


async def main():
    """Run the workspace cleanup E2E test suite."""
    test_runner = WorkspaceCleanupE2ETest()
    success = await test_runner.run_all_tests()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)