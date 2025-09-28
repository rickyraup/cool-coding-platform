#!/usr/bin/env python3
"""
Test script to verify file save sync functionality.
This simulates a save operation and checks if it syncs to the Docker container filesystem.
"""

import requests
import os
import json

# Configuration
API_BASE_URL = "http://localhost:8001"
SESSION_UUID = "106f0305-c080-4ba9-a64e-f8a7a102286f"
TEST_FILENAME = "test2.py"
NEW_CONTENT = """# Updated test content
x = 5
y = 10
print("Result:", x + y)
print("This file was updated via save test!")
"""

def test_save_sync():
    """Test the save functionality and verify sync to filesystem."""

    print("🔍 Testing file save sync functionality...")
    print(f"📁 Session UUID: {SESSION_UUID}")
    print(f"📄 Test file: {TEST_FILENAME}")

    # Step 1: Get current file content via API
    print("\n1️⃣ Getting current file content from API...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/workspace/{SESSION_UUID}/file/{TEST_FILENAME}")
        if response.status_code == 200:
            current_data = response.json()
            print(f"✅ Current content from API: {len(current_data['content'])} characters")
            print(f"📝 Preview: {current_data['content'][:50]}...")
        else:
            print(f"❌ Failed to get current content: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting current content: {e}")
        return False

    # Step 2: Check current filesystem content
    filesystem_path = f"/tmp/coding_platform_sessions/workspace_{SESSION_UUID}/{TEST_FILENAME}"
    print(f"\n2️⃣ Checking current filesystem content at {filesystem_path}...")
    try:
        with open(filesystem_path, 'r') as f:
            filesystem_content = f.read()
        print(f"✅ Current filesystem content: {len(filesystem_content)} characters")
        print(f"📝 Preview: {filesystem_content[:50]}...")
    except Exception as e:
        print(f"❌ Error reading filesystem: {e}")
        return False

    # Step 3: Save new content via API
    print(f"\n3️⃣ Saving new content via API...")
    print(f"📝 New content ({len(NEW_CONTENT)} characters):")
    print(NEW_CONTENT)

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/workspace/{SESSION_UUID}/file/{TEST_FILENAME}",
            headers={"Content-Type": "application/json"},
            json={"content": NEW_CONTENT}
        )
        if response.status_code == 200:
            save_result = response.json()
            print(f"✅ Save successful: {save_result['message']}")
        else:
            print(f"❌ Save failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during save: {e}")
        return False

    # Step 4: Check if filesystem was updated
    print(f"\n4️⃣ Verifying filesystem sync...")
    try:
        with open(filesystem_path, 'r') as f:
            updated_filesystem_content = f.read()

        print(f"📄 Updated filesystem content: {len(updated_filesystem_content)} characters")
        print(f"📝 Preview: {updated_filesystem_content[:50]}...")

        # Compare content
        if updated_filesystem_content.strip() == NEW_CONTENT.strip():
            print("✅ SUCCESS: Filesystem content matches saved content!")
            print("🔄 File save sync is working correctly!")
            return True
        else:
            print("❌ FAILURE: Filesystem content does not match!")
            print(f"Expected length: {len(NEW_CONTENT)}")
            print(f"Actual length: {len(updated_filesystem_content)}")
            print("\nExpected content:")
            print(repr(NEW_CONTENT))
            print("\nActual content:")
            print(repr(updated_filesystem_content))
            return False

    except Exception as e:
        print(f"❌ Error verifying filesystem sync: {e}")
        return False

if __name__ == "__main__":
    success = test_save_sync()
    print(f"\n{'='*50}")
    if success:
        print("🎉 TEST PASSED: File save sync is working correctly!")
    else:
        print("💥 TEST FAILED: File save sync has issues!")
    print(f"{'='*50}")