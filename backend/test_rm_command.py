#!/usr/bin/env python3
"""
Test script to verify rm command functionality.
Tests that rm deletes files from:
1. PostgreSQL database (WorkspaceItem removal)
2. Filesystem (mounted volume)
3. Docker container filesystem
"""

import asyncio
import requests
import subprocess
import json
import time
import os

async def test_rm_command():
    """Test that rm command deletes files from all required locations."""

    print("=== Testing Rm Command Functionality ===")

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

    # 3. Create test files first (to have something to delete)
    print("\n3. Creating test files to delete...")
    test_files = ["test_file1.py", "test_file2.txt", "test_file3.js"]

    for filename in test_files:
        file_data = {
            "file_path": filename,
            "content": f"# Test content for {filename}\nprint('This is {filename}')"
        }
        create_response = requests.post(
            f"http://localhost:8001/api/sessions/{session_id}/files",
            json=file_data
        )
        if create_response.status_code == 200:
            print(f"✓ Created {filename}")
        else:
            print(f"✗ Failed to create {filename}: {create_response.status_code}")

    # Give time for files to be created
    time.sleep(1)

    # 4. Verify files exist before deletion
    print("\n4. Verifying files exist before deletion...")

    # Check database
    workspace_response = requests.get(f"http://localhost:8001/api/sessions/{session_id}/workspace")
    if workspace_response.status_code == 200:
        workspace_items = workspace_response.json()
        existing_files = [item["full_path"] for item in workspace_items if not item.get("is_directory", False)]
        print(f"Files in database: {existing_files}")

        for filename in test_files:
            if filename in existing_files:
                print(f"✓ {filename} exists in database")
            else:
                print(f"✗ {filename} NOT found in database")
    else:
        print(f"✗ Failed to check database: {workspace_response.status_code}")

    # Check container
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

        if container_name:
            print(f"Found container: {container_name}")

            # List files in container
            ls_result = subprocess.run([
                "docker", "exec", container_name, "ls", "-la", "/app/"
            ], capture_output=True, text=True)

            if ls_result.returncode == 0:
                container_files = [line.split()[-1] for line in ls_result.stdout.strip().split('\n')
                                 if line and not line.startswith('d') and line.split()[-1] not in ['.', '..']]
                print(f"Files in container: {container_files}")
            else:
                print(f"Failed to list container files: {ls_result.stderr}")
        else:
            print("✗ No container found")
            return
    except Exception as e:
        print(f"✗ Error checking container: {e}")
        return

    # 5. Test rm command for single file
    print("\n5. Testing rm command for single file...")
    target_file = test_files[0]  # test_file1.py

    # Delete file via API
    delete_response = requests.delete(f"http://localhost:8001/api/sessions/{session_id}/files/{target_file}")
    if delete_response.status_code == 200:
        print(f"✓ Successfully executed rm command for {target_file}")
    else:
        print(f"✗ Failed to delete {target_file}: {delete_response.status_code} - {delete_response.text}")

    # 6. Verify file is deleted from DATABASE
    print("\n6. Verifying file deletion from database...")
    workspace_response = requests.get(f"http://localhost:8001/api/sessions/{session_id}/workspace")
    if workspace_response.status_code == 200:
        workspace_items = workspace_response.json()
        remaining_files = [item["full_path"] for item in workspace_items if not item.get("is_directory", False)]

        if target_file not in remaining_files:
            print(f"✓ {target_file} successfully removed from database")
        else:
            print(f"✗ {target_file} still exists in database")

        print(f"Remaining files in database: {remaining_files}")
    else:
        print(f"✗ Failed to check database after deletion: {workspace_response.status_code}")

    # 7. Verify file is deleted from FILESYSTEM (mounted volume)
    print("\n7. Verifying file deletion from mounted volume...")
    mounted_file_path = f"/tmp/coding_platform_sessions/workspace_{session_uuid}/{target_file}"
    if not os.path.exists(mounted_file_path):
        print(f"✓ {target_file} successfully removed from mounted volume")
    else:
        print(f"✗ {target_file} still exists in mounted volume: {mounted_file_path}")

    # 8. Verify file is deleted from DOCKER CONTAINER
    print("\n8. Verifying file deletion from Docker container...")
    try:
        check_result = subprocess.run([
            "docker", "exec", container_name, "test", "-f", f"/app/{target_file}"
        ], capture_output=True, text=True)

        if check_result.returncode != 0:
            print(f"✓ {target_file} successfully removed from Docker container")
        else:
            print(f"✗ {target_file} still exists in Docker container")

        # List remaining files in container
        ls_result = subprocess.run([
            "docker", "exec", container_name, "ls", "-la", "/app/"
        ], capture_output=True, text=True)

        if ls_result.returncode == 0:
            remaining_container_files = [line.split()[-1] for line in ls_result.stdout.strip().split('\n')
                                       if line and not line.startswith('d') and line.split()[-1] not in ['.', '..']]
            print(f"Remaining files in container: {remaining_container_files}")
        else:
            print(f"Failed to list remaining container files: {ls_result.stderr}")

    except Exception as e:
        print(f"✗ Error checking container after deletion: {e}")

    # 9. Test rm command for multiple files
    print("\n9. Testing rm command for multiple files...")
    remaining_files = test_files[1:]  # test_file2.txt, test_file3.js

    for filename in remaining_files:
        delete_response = requests.delete(f"http://localhost:8001/api/sessions/{session_id}/files/{filename}")
        if delete_response.status_code == 200:
            print(f"✓ Successfully deleted {filename}")
        else:
            print(f"✗ Failed to delete {filename}: {delete_response.status_code}")

    # 10. Verify all files are deleted
    print("\n10. Verifying all test files are deleted...")

    # Check database
    workspace_response = requests.get(f"http://localhost:8001/api/sessions/{session_id}/workspace")
    if workspace_response.status_code == 200:
        workspace_items = workspace_response.json()
        final_files = [item["full_path"] for item in workspace_items if not item.get("is_directory", False)]

        deleted_count = 0
        for filename in test_files:
            if filename not in final_files:
                print(f"✓ {filename} successfully deleted from database")
                deleted_count += 1
            else:
                print(f"✗ {filename} still exists in database")

        print(f"Summary: {deleted_count}/{len(test_files)} files successfully deleted from database")
        print(f"Final files in database: {final_files}")
    else:
        print(f"✗ Failed to check final database state: {workspace_response.status_code}")

    # Check container final state
    try:
        ls_result = subprocess.run([
            "docker", "exec", container_name, "ls", "-la", "/app/"
        ], capture_output=True, text=True)

        if ls_result.returncode == 0:
            final_container_files = [line.split()[-1] for line in ls_result.stdout.strip().split('\n')
                                   if line and not line.startswith('d') and line.split()[-1] not in ['.', '..']]

            deleted_count = 0
            for filename in test_files:
                if filename not in final_container_files:
                    print(f"✓ {filename} successfully deleted from container")
                    deleted_count += 1
                else:
                    print(f"✗ {filename} still exists in container")

            print(f"Summary: {deleted_count}/{len(test_files)} files successfully deleted from container")
            print(f"Final files in container: {final_container_files}")
        else:
            print(f"Failed to check final container state: {ls_result.stderr}")
    except Exception as e:
        print(f"✗ Error checking final container state: {e}")

    # 11. Test error handling - try to delete non-existent file
    print("\n11. Testing error handling for non-existent file...")
    nonexistent_file = "does_not_exist.txt"
    delete_response = requests.delete(f"http://localhost:8001/api/sessions/{session_id}/files/{nonexistent_file}")

    if delete_response.status_code == 404:
        print(f"✓ Correctly handled deletion of non-existent file: {nonexistent_file}")
    elif delete_response.status_code == 200:
        print(f"⚠ Deletion returned success for non-existent file (may be acceptable behavior)")
    else:
        print(f"✗ Unexpected response for non-existent file: {delete_response.status_code}")

    print("\n=== Rm Command Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_rm_command())