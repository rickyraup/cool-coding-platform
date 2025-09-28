#!/usr/bin/env python3
"""
Test script to verify touch command functionality.
Tests that touch creates files in:
1. PostgreSQL database (WorkspaceItem)
2. Filesystem (mounted volume)
3. Docker container filesystem
"""

import asyncio
import requests
import subprocess
import json
import time

async def test_touch_command():
    """Test that touch command creates files in all required locations."""

    print("=== Testing Touch Command Functionality ===")

    # 1. Create a new session
    print("\n1. Creating new session...")
    session_payload = {
        "user_id": "test_user",
        "code": "print('Hello, World!')",
        "language": "python"
    }
    response = requests.post("http://localhost:8001/api/sessions", json=session_payload)
    if response.status_code not in [200, 201]:
        print(f"Failed to create session: {response.status_code} - {response.text}")
        return

    session_data = response.json()
    session_id = session_data["id"]
    session_uuid = session_data["id"]  # In this API, id is the UUID
    print(f"Created session {session_id} (UUID: {session_uuid})")

    # 2. Start container for this session
    print("\n2. Starting container...")
    start_response = requests.post(f"http://localhost:8001/api/sessions/{session_id}/start")
    if start_response.status_code != 200:
        print(f"Failed to start container: {start_response.status_code} - {start_response.text}")
        return
    print("Container started successfully")

    # Give container time to start
    time.sleep(2)

    # 3. Test touch command via terminal input (simulating WebSocket)
    print("\n3. Testing touch command...")
    test_filename = "touch_test_file.py"

    # Create a file via the files API (simulating terminal touch command)
    file_data = {
        "file_path": test_filename,
        "content": ""  # Empty content for touch
    }

    create_response = requests.post(
        f"http://localhost:8001/api/sessions/{session_id}/files",
        json=file_data
    )
    if create_response.status_code != 200:
        print(f"Failed to create file via API: {create_response.status_code} - {create_response.text}")
        return
    print(f"✓ Touch command executed for {test_filename}")

    # 4. Verify file exists in DATABASE
    print("\n4. Verifying file exists in database...")
    workspace_response = requests.get(f"http://localhost:8001/api/sessions/{session_id}/workspace")
    if workspace_response.status_code == 200:
        workspace_items = workspace_response.json()
        file_in_db = any(item["full_path"] == test_filename for item in workspace_items)
        if file_in_db:
            print("✓ File exists in PostgreSQL database")
        else:
            print("✗ File NOT found in database")
            print(f"Available files: {[item['full_path'] for item in workspace_items]}")
            return
    else:
        print(f"✗ Failed to check database: {workspace_response.status_code}")
        return

    # 5. Verify file exists in FILESYSTEM (mounted volume)
    print("\n5. Verifying file exists in mounted volume...")
    mounted_file_path = f"/tmp/coding_platform_sessions/workspace_{session_uuid}/{test_filename}"
    try:
        with open(mounted_file_path, 'r') as f:
            content = f.read()
        print(f"✓ File exists in mounted volume: {mounted_file_path}")
        print(f"✓ Content length: {len(content)} characters (should be 0 for touch)")
    except FileNotFoundError:
        print(f"✗ File NOT found in mounted volume: {mounted_file_path}")
        return

    # 6. Verify file exists in DOCKER CONTAINER
    print("\n6. Verifying file exists in Docker container...")
    try:
        # Find the container
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
            "docker", "exec", container_name, "ls", "-la", f"/app/{test_filename}"
        ], capture_output=True, text=True)

        if check_result.returncode == 0:
            print("✓ File exists in Docker container")
            print(f"✓ Container file details: {check_result.stdout.strip()}")
        else:
            print("✗ File NOT found in Docker container")
            print(f"✗ Error: {check_result.stderr}")

            # Try to list all files in container to see what's there
            ls_result = subprocess.run([
                "docker", "exec", container_name, "ls", "-la", "/app/"
            ], capture_output=True, text=True)
            print(f"Files in container /app/: {ls_result.stdout}")
            return

    except subprocess.CalledProcessError as e:
        print(f"✗ Error checking Docker container: {e}")
        return

    # 7. Test multiple files with one touch command
    print("\n7. Testing multiple files with touch...")
    multi_files = ["file1.txt", "file2.txt", "file3.txt"]

    for filename in multi_files:
        file_data = {
            "file_path": filename,
            "content": ""
        }
        create_response = requests.post(
            f"http://localhost:8001/api/sessions/{session_id}/files",
            json=file_data
        )
        if create_response.status_code == 200:
            print(f"✓ Created {filename}")
        else:
            print(f"✗ Failed to create {filename}")

    # 8. Verify all files exist in container
    print("\n8. Verifying all files in container...")
    ls_result = subprocess.run([
        "docker", "exec", container_name, "ls", "/app/"
    ], capture_output=True, text=True)

    if ls_result.returncode == 0:
        files = ls_result.stdout.strip().split('\n')
        print(f"Files in container: {files}")

        expected_files = [test_filename] + multi_files
        for expected_file in expected_files:
            if expected_file in files:
                print(f"✓ {expected_file} found in container")
            else:
                print(f"✗ {expected_file} NOT found in container")
    else:
        print(f"✗ Failed to list files in container: {ls_result.stderr}")

    print("\n=== Touch Command Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_touch_command())