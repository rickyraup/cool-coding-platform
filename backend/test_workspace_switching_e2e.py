#!/usr/bin/env python3
"""
Step 12: Test workspace switching (full isolation + persistence)

This test verifies complete workspace isolation and persistence:
1. Create multiple isolated workspaces with different content
2. Switch between workspaces and verify complete isolation
3. Test file operations in each workspace independently  
4. Verify persistence after container restarts
5. Test concurrent access to different workspaces
6. Verify no cross-contamination between workspaces
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import time
from app.models.postgres_models import CodeSession, WorkspaceItem, User
from app.core.postgres import init_db
from app.services.container_manager import container_manager
from app.services.workspace_loader import workspace_loader


class WorkspaceSwitchingE2ETest:
    def __init__(self):
        self.base_url = "http://localhost:8002"
        
        # Create test workspaces
        self.workspaces = {
            "workspace_a": {
                "uuid": "19d05e0c-205d-4414-9acc-a092c9135444",  # Existing test session
                "name": "Workspace A - Python Dev",
                "files": {
                    "main.py": "# Workspace A Main\nprint('Hello from Workspace A!')\n\ndef workspace_a_function():\n    return 'Workspace A is working!'",
                    "config.json": '{"workspace": "A", "language": "python", "version": "1.0"}',
                    "utils/helper.py": "# Workspace A Utils\ndef helper_a():\n    return 'Helper from A'"
                }
            },
            "workspace_b": {
                "uuid": "ab17cbaf-872c-4d30-b825-2775b95c31ff",  # Different workspace 
                "name": "Workspace B - Web Dev", 
                "files": {
                    "main.py": "# Workspace B Main\nprint('Hello from Workspace B!')\n\ndef workspace_b_function():\n    return 'Workspace B is active!'",
                    "config.json": '{"workspace": "B", "language": "javascript", "version": "2.0"}',
                    "utils/helper.py": "# Workspace B Utils\ndef helper_b():\n    return 'Helper from B'"
                }
            }
        }
        
    def setup(self):
        """Initialize test environment."""
        print("🔧 Setting up workspace switching test environment...")
        
        # Initialize database
        init_db()
        
        # Verify both test sessions exist
        for workspace_id, workspace in self.workspaces.items():
            session = CodeSession.get_by_uuid(workspace["uuid"])
            if not session:
                print(f"❌ Test session {workspace['uuid']} ({workspace_id}) not found")
                return False
            print(f"✅ {workspace_id} session found: {session.name} (id: {session.id})")
            workspace["session_id"] = session.id
            workspace["session"] = session
            
        return True
    
    def test_basic_workspace_isolation(self):
        """Test basic isolation between workspaces."""
        print("\n🏠 Test 1: Basic Workspace Isolation")
        
        # Step 1: Set up Workspace A with unique content
        print("   📋 Setting up Workspace A...")
        workspace_a = self.workspaces["workspace_a"]
        
        # Start container for Workspace A
        start_response_a = requests.post(f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/container/start")
        if start_response_a.status_code != 200:
            print(f"   ❌ Failed to start Workspace A container: {start_response_a.status_code}")
            return False
        print("   ✅ Workspace A container started")
        
        # Create files in Workspace A
        for file_path, content in workspace_a["files"].items():
            create_payload = {"content": content}
            create_response = requests.post(
                f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/file/{file_path}",
                json=create_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if create_response.status_code != 200:
                print(f"   ❌ Failed to create {file_path} in Workspace A")
                return False
        print(f"   ✅ Created {len(workspace_a['files'])} files in Workspace A")
        
        # Step 2: Set up Workspace B with different content
        print("   📋 Setting up Workspace B...")
        workspace_b = self.workspaces["workspace_b"]
        
        # Start container for Workspace B (should be isolated)
        start_response_b = requests.post(f"{self.base_url}/api/session_workspace/{workspace_b['uuid']}/container/start")
        if start_response_b.status_code != 200:
            print(f"   ❌ Failed to start Workspace B container: {start_response_b.status_code}")
            return False
        print("   ✅ Workspace B container started")
        
        # Create files in Workspace B
        for file_path, content in workspace_b["files"].items():
            create_payload = {"content": content}
            create_response = requests.post(
                f"{self.base_url}/api/session_workspace/{workspace_b['uuid']}/file/{file_path}",
                json=create_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if create_response.status_code != 200:
                print(f"   ❌ Failed to create {file_path} in Workspace B")
                return False
        print(f"   ✅ Created {len(workspace_b['files'])} files in Workspace B")
        
        # Step 3: Verify isolation by checking content
        print("   🔍 Verifying workspace isolation...")
        
        # Check Workspace A files
        for file_path, expected_content in workspace_a["files"].items():
            get_response = requests.get(f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/file/{file_path}")
            if get_response.status_code != 200:
                print(f"   ❌ Failed to retrieve {file_path} from Workspace A")
                return False
                
            actual_content = get_response.json()['data']['content']
            if actual_content != expected_content:
                print(f"   ❌ Content mismatch in Workspace A {file_path}")
                return False
                
        # Check Workspace B files  
        for file_path, expected_content in workspace_b["files"].items():
            get_response = requests.get(f"{self.base_url}/api/session_workspace/{workspace_b['uuid']}/file/{file_path}")
            if get_response.status_code != 200:
                print(f"   ❌ Failed to retrieve {file_path} from Workspace B")
                return False
                
            actual_content = get_response.json()['data']['content']
            if actual_content != expected_content:
                print(f"   ❌ Content mismatch in Workspace B {file_path}")
                return False
                
        print("   ✅ Workspace isolation verified - files are correctly separated")
        return True
    
    def test_workspace_switching_persistence(self):
        """Test switching between workspaces and persistence."""
        print("\n🔄 Test 2: Workspace Switching & Persistence")
        
        # Step 1: Modify files in Workspace A
        print("   ✏️ Modifying files in Workspace A...")
        workspace_a = self.workspaces["workspace_a"]
        
        modified_content = f"""# Modified Workspace A - {time.time()}
print('Workspace A has been modified!')

def modified_function_a():
    return 'Modified at {time.time()}'
    
if __name__ == "__main__":
    print(modified_function_a())
"""
        
        update_payload = {"content": modified_content}
        update_response = requests.put(
            f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/file/main.py",
            json=update_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if update_response.status_code != 200:
            print("   ❌ Failed to modify Workspace A")
            return False
        print("   ✅ Modified main.py in Workspace A")
        
        # Step 2: Switch to Workspace B and verify it's unchanged
        print("   🔄 Switching to Workspace B...")
        
        get_b_response = requests.get(f"{self.base_url}/api/session_workspace/{self.workspaces['workspace_b']['uuid']}/file/main.py")
        if get_b_response.status_code != 200:
            print("   ❌ Failed to access Workspace B after switching")
            return False
            
        workspace_b_content = get_b_response.json()['data']['content']
        expected_b_content = self.workspaces["workspace_b"]["files"]["main.py"]
        
        if workspace_b_content != expected_b_content:
            print("   ❌ Workspace B was contaminated by changes to Workspace A")
            return False
        print("   ✅ Workspace B unchanged after modifying Workspace A")
        
        # Step 3: Save both workspaces and verify persistence
        print("   💾 Testing workspace persistence...")
        
        # Save Workspace A
        save_a_response = requests.post(f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/save")
        if save_a_response.status_code != 200:
            print("   ❌ Failed to save Workspace A")
            return False
            
        # Save Workspace B
        save_b_response = requests.post(f"{self.base_url}/api/session_workspace/{self.workspaces['workspace_b']['uuid']}/save")
        if save_b_response.status_code != 200:
            print("   ❌ Failed to save Workspace B")
            return False
        print("   ✅ Both workspaces saved to database")
        
        # Step 4: Verify database persistence
        print("   🔍 Verifying database persistence...")
        
        # Check Workspace A in database
        workspace_a_items = WorkspaceItem.get_all_by_session(workspace_a["session_id"])
        main_py_a = None
        for item in workspace_a_items:
            if item.name == "main.py" and item.type == "file":
                main_py_a = item
                break
                
        if not main_py_a or main_py_a.content != modified_content:
            print("   ❌ Workspace A changes not persisted to database")
            return False
            
        # Check Workspace B in database  
        workspace_b_items = WorkspaceItem.get_all_by_session(self.workspaces["workspace_b"]["session_id"])
        main_py_b = None
        for item in workspace_b_items:
            if item.name == "main.py" and item.type == "file":
                main_py_b = item
                break
                
        if not main_py_b or main_py_b.content != expected_b_content:
            print("   ❌ Workspace B persistence verification failed")
            return False
            
        print("   ✅ Workspace switching and persistence verified")
        return True
    
    async def test_concurrent_workspace_access(self):
        """Test concurrent access to different workspaces."""
        print("\n⚡ Test 3: Concurrent Workspace Access")
        
        # Step 1: Start both container sessions
        print("   🚀 Starting both workspace containers...")
        
        workspace_a = self.workspaces["workspace_a"]
        workspace_b = self.workspaces["workspace_b"]
        
        # Get or create container sessions concurrently
        session_a = await container_manager.get_or_create_session(str(workspace_a["session_id"]))
        session_b = await container_manager.get_or_create_session(str(workspace_b["session_id"]))
        
        if not session_a or not session_b:
            print("   ❌ Failed to create concurrent container sessions")
            return False
        
        print(f"   ✅ Both containers running: A={session_a.container_id[:12]}, B={session_b.container_id[:12]}")
        
        # Step 2: Perform concurrent file operations
        print("   📝 Performing concurrent file operations...")
        
        timestamp = int(time.time())
        
        # Create unique test files in each workspace simultaneously
        test_content_a = f"# Concurrent test A - {timestamp}\nprint('Concurrent A: {timestamp}')"
        test_content_b = f"# Concurrent test B - {timestamp}\nprint('Concurrent B: {timestamp}')"
        
        # Simulate concurrent API calls
        import threading
        import time
        
        results = {"a_success": False, "b_success": False}
        
        def create_file_a():
            try:
                create_payload = {"content": test_content_a}
                response = requests.post(
                    f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/file/concurrent_test_a.py",
                    json=create_payload,
                    headers={"Content-Type": "application/json"}
                )
                results["a_success"] = response.status_code == 200
            except Exception as e:
                print(f"   Error in thread A: {e}")
                
        def create_file_b():
            try:
                create_payload = {"content": test_content_b}
                response = requests.post(
                    f"{self.base_url}/api/session_workspace/{workspace_b['uuid']}/file/concurrent_test_b.py",
                    json=create_payload,
                    headers={"Content-Type": "application/json"}
                )
                results["b_success"] = response.status_code == 200
            except Exception as e:
                print(f"   Error in thread B: {e}")
        
        # Start both operations concurrently
        thread_a = threading.Thread(target=create_file_a)
        thread_b = threading.Thread(target=create_file_b)
        
        thread_a.start()
        thread_b.start()
        
        thread_a.join(timeout=10)
        thread_b.join(timeout=10)
        
        if not (results["a_success"] and results["b_success"]):
            print("   ❌ Concurrent file operations failed")
            return False
            
        print("   ✅ Concurrent file operations successful")
        
        # Step 3: Verify isolation after concurrent operations
        print("   🔍 Verifying isolation after concurrent operations...")
        
        # Check that each workspace has only its own file
        get_a_response = requests.get(f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/file/concurrent_test_a.py")
        get_b_response = requests.get(f"{self.base_url}/api/session_workspace/{workspace_b['uuid']}/file/concurrent_test_b.py")
        
        # Cross-contamination check
        get_a_wrong = requests.get(f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/file/concurrent_test_b.py")
        get_b_wrong = requests.get(f"{self.base_url}/api/session_workspace/{workspace_b['uuid']}/file/concurrent_test_a.py")
        
        if get_a_response.status_code != 200 or get_b_response.status_code != 200:
            print("   ❌ Failed to retrieve concurrent test files")
            return False
            
        if get_a_wrong.status_code == 200 or get_b_wrong.status_code == 200:
            print("   ❌ Cross-contamination detected between workspaces")
            return False
            
        print("   ✅ Concurrent access isolation verified")
        return True
    
    async def test_container_restart_persistence(self):
        """Test workspace persistence across container restarts."""
        print("\n🔄 Test 4: Container Restart Persistence")
        
        workspace_a = self.workspaces["workspace_a"]
        
        # Step 1: Create unique content
        print("   📝 Creating unique content for restart test...")
        restart_content = f"""# Restart persistence test - {time.time()}
import datetime

def restart_test():
    return f"Persisted across restart: {{datetime.datetime.now()}}"
    
if __name__ == "__main__":
    print(restart_test())
"""
        
        create_payload = {"content": restart_content}
        create_response = requests.post(
            f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/file/restart_test.py",
            json=create_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if create_response.status_code != 200:
            print("   ❌ Failed to create restart test file")
            return False
        print("   ✅ Created restart test file")
        
        # Step 2: Save workspace
        print("   💾 Saving workspace before restart...")
        save_response = requests.post(f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/save")
        if save_response.status_code != 200:
            print("   ❌ Failed to save workspace")
            return False
        print("   ✅ Workspace saved")
        
        # Step 3: Force container cleanup
        print("   🧹 Forcing container cleanup...")
        session_str = str(workspace_a["session_id"])
        active_session_id = container_manager.find_session_by_workspace_id(session_str)
        
        if active_session_id:
            await container_manager.cleanup_session(active_session_id)
            print(f"   ✅ Container {active_session_id} cleaned up")
        
        # Wait a moment for cleanup to complete
        await asyncio.sleep(2)
        
        # Step 4: Restart container and load workspace
        print("   🚀 Restarting container and loading workspace...")
        restart_response = requests.post(f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/container/start")
        if restart_response.status_code != 200:
            print("   ❌ Failed to restart container")
            return False
        print("   ✅ Container restarted")
        
        # Step 5: Verify persistence
        print("   🔍 Verifying persistence after restart...")
        get_response = requests.get(f"{self.base_url}/api/session_workspace/{workspace_a['uuid']}/file/restart_test.py")
        if get_response.status_code != 200:
            print("   ❌ Restart test file not found after restart")
            return False
            
        retrieved_content = get_response.json()['data']['content']
        if retrieved_content == restart_content:
            print("   ✅ Workspace persisted correctly across container restart")
        else:
            print("   ❌ Workspace content changed after restart")
            return False
            
        return True
    
    async def run_all_tests(self):
        """Run all workspace switching tests."""
        print("🧪 Starting Workspace Switching E2E Tests")
        print("=" * 60)
        
        if not self.setup():
            return False
            
        tests = [
            ("Basic Workspace Isolation", self.test_basic_workspace_isolation),
            ("Workspace Switching & Persistence", self.test_workspace_switching_persistence),
            ("Concurrent Workspace Access", self.test_concurrent_workspace_access),
            ("Container Restart Persistence", self.test_container_restart_persistence),
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
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
                failed += 1
                
        print("\n" + "=" * 60)
        print(f"🧪 Workspace Switching E2E Test Results:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
        
        if failed == 0:
            print("🎉 ALL WORKSPACE SWITCHING E2E TESTS PASSED!")
            print("✅ Step 12: Workspace switching (full isolation + persistence) - COMPLETE")
            return True
        else:
            print("❌ Some tests failed")
            return False


async def main():
    """Run the workspace switching E2E test suite."""
    test_runner = WorkspaceSwitchingE2ETest()
    success = await test_runner.run_all_tests()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)