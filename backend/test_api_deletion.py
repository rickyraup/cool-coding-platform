#!/usr/bin/env python3
"""
Test API-based file deletion to verify container sync functionality.
"""

import requests
import os
import time
import subprocess

SESSION_UUID = "106f0305-c080-4ba9-a64e-f8a7a102286f"
TEST_FILENAME = "test_api_deletion.py"
BASE_URL = "http://localhost:8001"
SESSIONS_DIR = "/tmp/coding_platform_sessions"

def create_test_file():
    """Create a test file directly in workspace directory."""
    workspace_dir = os.path.join(SESSIONS_DIR, f"workspace_{SESSION_UUID}")
    test_file_path = os.path.join(workspace_dir, TEST_FILENAME)

    # Ensure workspace directory exists
    os.makedirs(workspace_dir, exist_ok=True)

    test_content = "# Test file for API deletion\nprint('This file should be deleted via API')\nx = 123\n"
    with open(test_file_path, 'w') as f:
        f.write(test_content)

    print(f"✅ Created test file: {test_file_path}")
    return test_file_path

def check_file_exists(file_path):
    """Check if file exists."""
    exists = os.path.exists(file_path)
    print(f"📁 File {file_path} exists: {exists}")
    return exists

def check_docker_container():
    """Check if there's a Docker container for this session."""
    try:
        result = subprocess.run([
            "docker", "ps", "--filter", f"name=.*{SESSION_UUID}.*", "--format", "{{.ID}}"
        ], capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            container_id = result.stdout.strip().split('\n')[0]
            print(f"🐳 Found Docker container: {container_id}")
            return container_id
        else:
            print("❌ No Docker container found for session")
            return None
    except Exception as e:
        print(f"❌ Error checking Docker container: {e}")
        return None

def check_file_in_container(container_id, filename):
    """Check if file exists inside Docker container."""
    try:
        result = subprocess.run([
            "docker", "exec", container_id, "ls", "-la", f"/app/{filename}"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"🐳 File {filename} exists in container")
            return True
        else:
            print(f"🐳 File {filename} does not exist in container")
            return False
    except Exception as e:
        print(f"❌ Error checking file in container: {e}")
        return False

def test_api_deletion():
    """Test file deletion through API."""
    print("🧪 TESTING API-BASED FILE DELETION")
    print("=" * 60)

    # Step 1: Create test file
    test_file_path = create_test_file()

    # Step 2: Verify file exists before deletion
    print(f"\n🔍 Checking file before deletion...")
    if not check_file_exists(test_file_path):
        print("❌ Test file doesn't exist, cannot proceed")
        return False

    # Step 3: Check Docker container state
    container_id = check_docker_container()
    if container_id:
        file_in_container_before = check_file_in_container(container_id, TEST_FILENAME)
        print(f"🐳 File in container before deletion: {file_in_container_before}")

    # Step 4: Call API to delete file
    print(f"\n🗑️ Calling API to delete file: {TEST_FILENAME}")
    delete_url = f"{BASE_URL}/api/session-workspace/{SESSION_UUID}/file/{TEST_FILENAME}"

    try:
        response = requests.delete(delete_url)
        print(f"📡 API Response Status: {response.status_code}")
        print(f"📡 API Response Body: {response.text}")

        if response.status_code == 200:
            print("✅ API call successful")
        else:
            print(f"❌ API call failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ API call failed with error: {e}")
        return False

    # Step 5: Verify file is deleted from filesystem
    print(f"\n🔍 Checking file after deletion...")
    time.sleep(1)  # Wait a moment for deletion

    file_exists_after = check_file_exists(test_file_path)

    # Step 6: Check Docker container state after deletion
    if container_id:
        file_in_container_after = check_file_in_container(container_id, TEST_FILENAME)
        print(f"🐳 File in container after deletion: {file_in_container_after}")

    # Step 7: Evaluate results
    print(f"\n📊 RESULTS:")
    print(f"  File deleted from filesystem: {not file_exists_after}")
    if container_id:
        container_sync_success = not file_in_container_after if 'file_in_container_before' in locals() else True
        print(f"  File deleted from container: {container_sync_success}")

        if not file_exists_after and container_sync_success:
            print("🎉 SUCCESS: File deletion and container sync working!")
            return True
        else:
            print("💥 FAILURE: File deletion or container sync has issues")
            return False
    else:
        if not file_exists_after:
            print("🎉 SUCCESS: File deletion working (no container to test)")
            return True
        else:
            print("💥 FAILURE: File deletion not working")
            return False

if __name__ == "__main__":
    success = test_api_deletion()
    exit(0 if success else 1)