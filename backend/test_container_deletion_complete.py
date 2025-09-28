#!/usr/bin/env python3
"""
Test script to verify complete file deletion from Docker container.
This test ensures files are deleted from:
1. Docker mounted volume
2. Inside Docker container filesystem
3. Database (WorkspaceItem)
"""

import asyncio
import subprocess
import requests
import json
import time

async def test_container_file_deletion():
    """Test that file deletion works for an active container session."""

    print("=== Testing Complete Container File Deletion ===")

    # 1. Create a new session
    print("\n1. Creating new session...")
    response = requests.post("http://localhost:8000/api/sessions")
    if response.status_code != 200:
        print(f"Failed to create session: {response.status_code} - {response.text}")
        return

    session_data = response.json()
    session_id = session_data["id"]
    session_uuid = session_data["uuid"]
    print(f"Created session {session_id} (UUID: {session_uuid})")

    # 2. Start container for this session
    print("\n2. Starting container...")
    start_response = requests.post(f"http://localhost:8000/api/sessions/{session_id}/start")
    if start_response.status_code != 200:
        print(f"Failed to start container: {start_response.status_code} - {start_response.text}")
        return
    print("Container started successfully")

    # 3. Create a test file
    print("\n3. Creating test file...")
    file_content = "print('This file should be completely deleted')\nprint('From all locations')"
    file_data = {
        "file_path": "test_complete_deletion.py",
        "content": file_content
    }

    create_response = requests.post(
        f"http://localhost:8000/api/sessions/{session_id}/files",
        json=file_data
    )
    if create_response.status_code != 200:
        print(f"Failed to create file: {create_response.status_code} - {create_response.text}")
        return
    print("Test file created successfully")

    # 4. Verify file exists in all locations BEFORE deletion
    print("\n4. Verifying file exists in all locations...")

    # Check mounted volume
    mounted_file_path = f"/tmp/coding_platform_sessions/workspace_{session_uuid}/test_complete_deletion.py"
    try:
        with open(mounted_file_path, 'r') as f:
            content = f.read()
        print(f"✓ File exists in mounted volume: {len(content)} characters")
    except FileNotFoundError:
        print("✗ File NOT found in mounted volume")
        return

    # Check Docker container using docker exec
    try:
        result = subprocess.run([
            "docker", "ps", "--filter", f"name=workspace_{session_uuid}", "--format", "{{.Names}}"
        ], capture_output=True, text=True, check=True)

        container_names = result.stdout.strip().split('\n')
        container_name = None
        for name in container_names:
            if name and f"workspace_{session_uuid}" in name:
                container_name = name
                break

        if not container_name:
            print("✗ No active container found")
            return

        print(f"Found container: {container_name}")

        # Check if file exists in container
        check_result = subprocess.run([
            "docker", "exec", container_name, "ls", "/app/test_complete_deletion.py"
        ], capture_output=True, text=True)

        if check_result.returncode == 0:
            print("✓ File exists in Docker container")
        else:
            print("✗ File NOT found in Docker container")
            return

    except subprocess.CalledProcessError as e:
        print(f"✗ Error checking Docker container: {e}")
        return

    # Check database
    workspace_response = requests.get(f"http://localhost:8000/api/sessions/{session_id}/workspace")
    if workspace_response.status_code == 200:
        workspace_items = workspace_response.json()
        test_file_in_db = any(item["full_path"] == "test_complete_deletion.py" for item in workspace_items)
        if test_file_in_db:
            print("✓ File exists in database")
        else:
            print("✗ File NOT found in database")
            return
    else:
        print(f"✗ Failed to check database: {workspace_response.status_code}")
        return

    # 5. Delete the file
    print("\n5. Deleting test file...")
    delete_response = requests.delete(f"http://localhost:8000/api/sessions/{session_id}/files/test_complete_deletion.py")
    if delete_response.status_code != 200:
        print(f"Failed to delete file: {delete_response.status_code} - {delete_response.text}")
        return
    print("Delete request completed successfully")

    # 6. Verify file is deleted from all locations AFTER deletion
    print("\n6. Verifying file is deleted from all locations...")

    # Check mounted volume
    try:
        with open(mounted_file_path, 'r') as f:
            content = f.read()
        print("✗ File STILL exists in mounted volume")
    except FileNotFoundError:
        print("✓ File successfully deleted from mounted volume")

    # Check Docker container
    check_result = subprocess.run([
        "docker", "exec", container_name, "ls", "/app/test_complete_deletion.py"
    ], capture_output=True, text=True)

    if check_result.returncode == 0:
        print("✗ File STILL exists in Docker container")
        print("This is the bug we're trying to fix!")
    else:
        print("✓ File successfully deleted from Docker container")

    # Check database
    workspace_response = requests.get(f"http://localhost:8000/api/sessions/{session_id}/workspace")
    if workspace_response.status_code == 200:
        workspace_items = workspace_response.json()
        test_file_in_db = any(item["full_path"] == "test_complete_deletion.py" for item in workspace_items)
        if test_file_in_db:
            print("✗ File STILL exists in database")
        else:
            print("✓ File successfully deleted from database")
    else:
        print(f"✗ Failed to check database after deletion: {workspace_response.status_code}")

    # 7. Test ls command in container to see current files
    print("\n7. Testing ls command in container...")
    ls_result = subprocess.run([
        "docker", "exec", container_name, "ls", "/app/"
    ], capture_output=True, text=True)

    if ls_result.returncode == 0:
        files = ls_result.stdout.strip().split('\n')
        print(f"Files in container: {files}")
        if "test_complete_deletion.py" in files:
            print("✗ PROBLEM: Deleted file still appears in ls output")
        else:
            print("✓ SUCCESS: Deleted file no longer appears in ls output")
    else:
        print(f"✗ Failed to run ls in container: {ls_result.stderr}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_container_file_deletion())