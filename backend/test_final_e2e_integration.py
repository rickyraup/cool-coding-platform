#!/usr/bin/env python3
"""
Step 13: Final E2E Integration Test Across Multiple Workspaces

This comprehensive test validates the complete file system architecture:
1. End-to-end workflow across multiple workspaces
2. Full integration: PostgreSQL → Docker → API → UI simulation
3. Complete file lifecycle: create → load → fetch → update → persist → cleanup
4. Cross-workspace isolation and data integrity
5. Performance and reliability under realistic usage patterns
6. System resilience and error recovery
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


class FinalE2EIntegrationTest:
    def __init__(self):
        self.base_url = "http://localhost:8002"
        
        # Multi-workspace test scenario
        self.workspaces = {
            "python_dev": {
                "uuid": "19d05e0c-205d-4414-9acc-a092c9135444",
                "name": "Python Development Workspace",
                "session_id": 14,
                "files": {
                    "main.py": "# Python Development Environment\nimport numpy as np\nimport pandas as pd\n\ndef analyze_data():\n    data = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})\n    return data.mean()\n\nif __name__ == '__main__':\n    print('Python Development Environment')\n    result = analyze_data()\n    print(f'Analysis result: {result}')",
                    "utils.py": "def helper_function():\n    return 'Python utility function'",
                    "config.json": '{"environment": "python", "version": "3.11", "packages": ["numpy", "pandas"]}',
                    "data/sample.csv": "name,age,city\nAlice,25,NYC\nBob,30,LA\nCharlie,35,Chicago",
                    "tests/test_main.py": "import unittest\nfrom main import analyze_data\n\nclass TestMain(unittest.TestCase):\n    def test_analyze_data(self):\n        result = analyze_data()\n        self.assertIsNotNone(result)\n\nif __name__ == '__main__':\n    unittest.main()"
                }
            },
            "web_dev": {
                "uuid": "ab17cbaf-872c-4d30-b825-2775b95c31ff",
                "name": "Web Development Workspace", 
                "session_id": 15,
                "files": {
                    "main.py": "# Web Development Environment\nfrom flask import Flask, jsonify\n\napp = Flask(__name__)\n\n@app.route('/api/health')\ndef health_check():\n    return jsonify({'status': 'healthy', 'service': 'web-dev'})\n\n@app.route('/api/data')\ndef get_data():\n    return jsonify({'message': 'Hello from web dev workspace'})\n\nif __name__ == '__main__':\n    print('Web Development Server Starting...')\n    app.run(debug=True, port=5000)",
                    "static/style.css": "body { font-family: Arial, sans-serif; margin: 20px; }",
                    "templates/index.html": "<html><body><h1>Web Development Workspace</h1></body></html>",
                    "config.json": '{"environment": "web", "framework": "flask", "port": 5000}',
                    "requirements.txt": "flask==2.3.3\nrequests==2.31.0"
                }
            }
        }
        
    def setup(self):
        """Initialize comprehensive test environment."""
        print("🔧 Setting up comprehensive E2E test environment...")
        
        # Initialize database
        init_db()
        
        # Verify both workspace sessions exist
        all_workspaces_ready = True
        for workspace_name, workspace_data in self.workspaces.items():
            session = CodeSession.get_by_uuid(workspace_data["uuid"])
            if not session:
                print(f"❌ Workspace {workspace_name} session {workspace_data['uuid']} not found")
                all_workspaces_ready = False
            else:
                workspace_data["session"] = session
                print(f"✅ {workspace_name} workspace ready: {session.name} (id: {session.id})")
                
        return all_workspaces_ready
    
    async def test_complete_file_lifecycle(self):
        """Test complete file lifecycle across multiple operations."""
        print("\n📁 Test 1: Complete File Lifecycle")
        
        workspace = self.workspaces["python_dev"]
        session_uuid = workspace["uuid"]
        
        print("   🚀 Starting container session...")
        start_response = requests.post(f"{self.base_url}/api/session_workspace/{session_uuid}/container/start")
        if start_response.status_code != 200:
            print(f"   ❌ Failed to start container: {start_response.status_code}")
            return False
        
        # 1. Create multiple files with complex structure
        print("   📝 Creating complex file structure...")
        for file_path, content in workspace["files"].items():
            create_payload = {"content": content}
            create_response = requests.post(
                f"{self.base_url}/api/session_workspace/{session_uuid}/file/{file_path}",
                json=create_payload,
                headers={"Content-Type": "application/json"}
            )
            if create_response.status_code != 200:
                print(f"   ❌ Failed to create {file_path}")
                return False
        print(f"   ✅ Created {len(workspace['files'])} files successfully")
        
        # 2. Fetch and verify all files
        print("   🔍 Verifying file contents...")
        for file_path, expected_content in workspace["files"].items():
            get_response = requests.get(f"{self.base_url}/api/session_workspace/{session_uuid}/file/{file_path}")
            if get_response.status_code != 200:
                print(f"   ❌ Failed to fetch {file_path}")
                return False
            
            actual_content = get_response.json()["data"]["content"]
            if actual_content != expected_content:
                print(f"   ❌ Content mismatch for {file_path}")
                return False
        print("   ✅ All file contents verified")
        
        # 3. Update files and verify changes
        print("   ✏️ Testing file updates...")
        update_content = workspace["files"]["main.py"] + "\n\n# Updated with integration test timestamp\ntest_timestamp = " + str(int(time.time()))
        update_payload = {"content": update_content}
        update_response = requests.put(
            f"{self.base_url}/api/session_workspace/{session_uuid}/file/main.py",
            json=update_payload,
            headers={"Content-Type": "application/json"}
        )
        if update_response.status_code != 200:
            print("   ❌ Failed to update main.py")
            return False
        
        # Verify update
        verify_response = requests.get(f"{self.base_url}/api/session_workspace/{session_uuid}/file/main.py")
        if verify_response.json()["data"]["content"] != update_content:
            print("   ❌ Update verification failed")
            return False
        print("   ✅ File update verified")
        
        # 4. Test workspace tree structure
        print("   🌳 Verifying workspace tree structure...")
        tree_response = requests.get(f"{self.base_url}/api/session_workspace/{session_uuid}/workspace/tree")
        if tree_response.status_code != 200:
            print("   ❌ Failed to get workspace tree")
            return False
        
        tree_data = tree_response.json()["data"]
        # Should have root level files and directories
        expected_items = ["main.py", "utils.py", "config.json", "data", "tests"]
        actual_items = [item["name"] for item in tree_data]
        for expected_item in expected_items:
            if expected_item not in actual_items:
                print(f"   ❌ Missing expected item: {expected_item}")
                return False
        print("   ✅ Workspace tree structure verified")
        
        # 5. Persist to database and verify
        print("   💾 Testing workspace persistence...")
        save_response = requests.post(f"{self.base_url}/api/session_workspace/{session_uuid}/save")
        if save_response.status_code != 200:
            print("   ❌ Failed to save workspace")
            return False
        
        # Verify in database
        session = workspace["session"]
        workspace_items = WorkspaceItem.get_all_by_session(session.id)
        if len(workspace_items) < len(workspace["files"]):
            print(f"   ❌ Insufficient items in database: {len(workspace_items)} < {len(workspace['files'])}")
            return False
        print("   ✅ Workspace persistence verified")
        
        return True
    
    async def test_multi_workspace_isolation(self):
        """Test complete isolation between multiple active workspaces."""
        print("\n🔒 Test 2: Multi-Workspace Isolation Under Load")
        
        # Start both workspaces
        print("   🚀 Starting both workspace containers...")
        for workspace_name, workspace_data in self.workspaces.items():
            start_response = requests.post(f"{self.base_url}/api/session_workspace/{workspace_data['uuid']}/container/start")
            if start_response.status_code != 200:
                print(f"   ❌ Failed to start {workspace_name} container")
                return False
        
        # Create different content in each workspace simultaneously
        print("   📝 Creating workspace-specific content...")
        tasks = []
        
        for workspace_name, workspace_data in self.workspaces.items():
            session_uuid = workspace_data["uuid"]
            
            # Create workspace-specific marker files
            marker_content = f"# {workspace_name.upper()} WORKSPACE MARKER\n# Created at: {time.time()}\n# Workspace: {workspace_name}\n\ndef get_workspace_id():\n    return '{workspace_name}'\n\nprint('This is {workspace_name}')"
            
            create_payload = {"content": marker_content}
            create_response = requests.post(
                f"{self.base_url}/api/session_workspace/{session_uuid}/file/workspace_marker.py",
                json=create_payload,
                headers={"Content-Type": "application/json"}
            )
            if create_response.status_code != 200:
                print(f"   ❌ Failed to create marker for {workspace_name}")
                return False
        
        # Verify isolation by checking each workspace only has its own marker
        print("   🔍 Verifying cross-workspace isolation...")
        await asyncio.sleep(1)  # Allow operations to complete
        
        for workspace_name, workspace_data in self.workspaces.items():
            session_uuid = workspace_data["uuid"]
            
            # Check marker file exists and has correct content
            marker_response = requests.get(f"{self.base_url}/api/session_workspace/{session_uuid}/file/workspace_marker.py")
            if marker_response.status_code != 200:
                print(f"   ❌ Marker file not found in {workspace_name}")
                return False
                
            marker_content = marker_response.json()["data"]["content"]
            if workspace_name not in marker_content:
                print(f"   ❌ Incorrect marker content in {workspace_name}")
                return False
        
        print("   ✅ Multi-workspace isolation verified")
        return True
    
    async def test_system_resilience(self):
        """Test system resilience under various conditions."""
        print("\n💪 Test 3: System Resilience and Error Recovery")
        
        workspace = self.workspaces["python_dev"]
        session_uuid = workspace["uuid"]
        
        # Test 1: Container restart resilience
        print("   🔄 Testing container restart resilience...")
        
        # Create test content
        resilience_content = f"# Resilience test content\ntest_data = {{'timestamp': {time.time()}, 'test': 'resilience'}}\nprint('Resilience test')"
        create_payload = {"content": resilience_content}
        requests.post(
            f"{self.base_url}/api/session_workspace/{session_uuid}/file/resilience_test.py",
            json=create_payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Force container cleanup and restart
        cleanup_response = requests.post(f"{self.base_url}/api/session_workspace/{session_uuid}/container/cleanup")
        if cleanup_response.status_code != 200:
            print("   ❌ Failed to cleanup container")
            return False
        
        await asyncio.sleep(2)  # Allow cleanup to complete
        
        # Restart and verify content persisted
        start_response = requests.post(f"{self.base_url}/api/session_workspace/{session_uuid}/container/start")
        if start_response.status_code != 200:
            print("   ❌ Failed to restart container")
            return False
        
        # Verify content survived restart
        verify_response = requests.get(f"{self.base_url}/api/session_workspace/{session_uuid}/file/resilience_test.py")
        if verify_response.status_code != 200:
            print("   ❌ Content not found after restart")
            return False
        
        if verify_response.json()["data"]["content"] != resilience_content:
            print("   ❌ Content corrupted after restart")
            return False
        
        print("   ✅ Container restart resilience verified")
        
        # Test 2: Error handling for invalid operations
        print("   🚫 Testing error handling...")
        
        # Test invalid file path
        invalid_response = requests.get(f"{self.base_url}/api/session_workspace/{session_uuid}/file/nonexistent/path/file.py")
        if invalid_response.status_code == 200:
            print("   ❌ Invalid file request should fail")
            return False
        
        # Test invalid session UUID
        invalid_session = "00000000-0000-0000-0000-000000000000"
        invalid_session_response = requests.get(f"{self.base_url}/api/session_workspace/{invalid_session}/file/test.py")
        if invalid_session_response.status_code != 404:
            print("   ❌ Invalid session should return 404")
            return False
        
        print("   ✅ Error handling verified")
        return True
    
    async def test_performance_under_load(self):
        """Test performance characteristics under realistic load."""
        print("\n⚡ Test 4: Performance Under Load")
        
        workspace = self.workspaces["web_dev"]
        session_uuid = workspace["uuid"]
        
        print("   📊 Testing multiple file operations performance...")
        
        start_time = time.time()
        operation_count = 20
        
        # Create multiple files rapidly
        for i in range(operation_count):
            file_content = f"# Performance test file {i}\ntest_data_{i} = {{'index': {i}, 'timestamp': {time.time()}}}\n\ndef test_function_{i}():\n    return 'Performance test {i}'"
            create_payload = {"content": file_content}
            
            response = requests.post(
                f"{self.base_url}/api/session_workspace/{session_uuid}/file/perf_test_{i}.py",
                json=create_payload,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code != 200:
                print(f"   ❌ Failed to create performance test file {i}")
                return False
        
        create_time = time.time() - start_time
        print(f"   📝 Created {operation_count} files in {create_time:.2f}s ({operation_count/create_time:.1f} files/sec)")
        
        # Read all files back
        read_start = time.time()
        for i in range(operation_count):
            response = requests.get(f"{self.base_url}/api/session_workspace/{session_uuid}/file/perf_test_{i}.py")
            if response.status_code != 200:
                print(f"   ❌ Failed to read performance test file {i}")
                return False
        
        read_time = time.time() - read_start
        print(f"   📖 Read {operation_count} files in {read_time:.2f}s ({operation_count/read_time:.1f} files/sec)")
        
        # Performance thresholds (reasonable for development environment)
        if create_time > 10:  # Should create 20 files in under 10 seconds
            print(f"   ⚠️ File creation performance concern: {create_time:.2f}s")
        else:
            print("   ✅ File creation performance acceptable")
        
        if read_time > 5:  # Should read 20 files in under 5 seconds
            print(f"   ⚠️ File read performance concern: {read_time:.2f}s")
        else:
            print("   ✅ File read performance acceptable")
        
        return True
    
    async def test_data_integrity(self):
        """Test data integrity across the entire system."""
        print("\n🔒 Test 5: End-to-End Data Integrity")
        
        # Test data integrity across multiple operations
        print("   🔐 Testing data integrity across complex operations...")
        
        integrity_data = {
            "binary_test.py": "# Binary content test\nimport base64\ndata = b'\\x00\\x01\\x02\\x03\\xff\\xfe\\xfd'\nencoded = base64.b64encode(data)\nprint(encoded)",
            "unicode_test.py": "# Unicode content test\n# 测试中文\n# тест русский\n# テスト日本語\ndef unicode_function():\n    return '🚀 Unicode test successful! 🎉'",
            "large_test.py": "# Large file test\n" + "# " + "x" * 1000 + "\n" + "data = [" + ", ".join([str(i) for i in range(100)]) + "]\n" + "print('Large file test')",
        }
        
        workspace = self.workspaces["python_dev"]
        session_uuid = workspace["uuid"]
        
        # Create test files
        for file_path, content in integrity_data.items():
            create_payload = {"content": content}
            response = requests.post(
                f"{self.base_url}/api/session_workspace/{session_uuid}/file/{file_path}",
                json=create_payload,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code != 200:
                print(f"   ❌ Failed to create integrity test file: {file_path}")
                return False
        
        # Force save to database
        requests.post(f"{self.base_url}/api/session_workspace/{session_uuid}/save")
        
        # Restart container to force reload from database
        requests.post(f"{self.base_url}/api/session_workspace/{session_uuid}/container/cleanup")
        await asyncio.sleep(1)
        requests.post(f"{self.base_url}/api/session_workspace/{session_uuid}/container/start")
        
        # Verify all content is identical
        for file_path, expected_content in integrity_data.items():
            response = requests.get(f"{self.base_url}/api/session_workspace/{session_uuid}/file/{file_path}")
            if response.status_code != 200:
                print(f"   ❌ Failed to read integrity test file: {file_path}")
                return False
            
            actual_content = response.json()["data"]["content"]
            if actual_content != expected_content:
                print(f"   ❌ Data integrity violation in {file_path}")
                print(f"   Expected length: {len(expected_content)}, Actual length: {len(actual_content)}")
                return False
        
        print("   ✅ Data integrity verified across full system cycle")
        return True
    
    async def run_all_tests(self):
        """Run comprehensive E2E integration test suite."""
        print("🧪 Starting Final E2E Integration Test Suite")
        print("=" * 70)
        
        if not self.setup():
            return False
            
        tests = [
            ("Complete File Lifecycle", self.test_complete_file_lifecycle),
            ("Multi-Workspace Isolation Under Load", self.test_multi_workspace_isolation),
            ("System Resilience and Error Recovery", self.test_system_resilience),
            ("Performance Under Load", self.test_performance_under_load),
            ("End-to-End Data Integrity", self.test_data_integrity),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"\n{'=' * 50}")
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
                
        print("\n" + "=" * 70)
        print(f"🧪 Final E2E Integration Test Results:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL E2E INTEGRATION TESTS PASSED!")
            print("✅ Step 13: Final e2e integration test across multiple workspaces - COMPLETE")
            print("\n🏆 COMPREHENSIVE FILE SYSTEM ARCHITECTURE REVIEW COMPLETE!")
            print("   All 13 steps have been successfully implemented and tested.")
            return True
        else:
            print("❌ Some integration tests failed")
            return False


async def main():
    """Run the final comprehensive E2E integration test suite."""
    test_runner = FinalE2EIntegrationTest()
    success = await test_runner.run_all_tests()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)