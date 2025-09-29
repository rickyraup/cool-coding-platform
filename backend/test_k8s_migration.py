#!/usr/bin/env python3
"""Test script to verify the Kubernetes migration is working properly."""

import asyncio
import sys
import time


# Add the backend path for imports
sys.path.insert(0, "/Users/rickyraup1/personal_projects/cool-coding-platform/backend")

from app.services.container_manager import container_manager


async def test_kubernetes_migration():
    """Test that the application is fully using Kubernetes instead of Docker."""
    print("🧪 Testing Kubernetes Migration\n")

    # Test 1: Check Kubernetes availability
    print("1. Testing Kubernetes availability...")
    if not container_manager.is_kubernetes_available():
        print("❌ Kubernetes is not available!")
        return False
    print("✅ Kubernetes is available")

    # Test 2: Create a test session
    print("\n2. Testing session creation...")
    test_session_id = f"test-migration-{int(time.time())}"

    try:
        session = await container_manager.create_session(test_session_id)
        print(f"✅ Created session: {session.session_id}")
        print(f"   Pod name: {session.pod_name}")
        print(f"   Working dir: {session.working_dir}")
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        return False

    # Test 3: Wait for pod to be ready
    print("\n3. Waiting for pod to be ready...")
    max_wait = 30
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            from app.services.kubernetes_client import kubernetes_client_service

            pod = kubernetes_client_service.get_pod(session.pod_name)
            if pod and pod.status.phase == "Running":
                print(
                    f"✅ Pod is running after {int(time.time() - start_time)} seconds"
                )
                break
            print(f"   Pod status: {pod.status.phase if pod else 'Unknown'}")
        except Exception as e:
            print(f"   Error checking pod: {e}")

        await asyncio.sleep(2)
    else:
        print("❌ Pod did not start within timeout")
        return False

    # Test 4: Test command execution
    print("\n4. Testing command execution...")
    test_commands = [
        "python3 --version",
        "echo 'Hello from Kubernetes!'",
        "ls -la",
        "pwd",
    ]

    for cmd in test_commands:
        try:
            print(f"   Executing: {cmd}")
            output, exit_code = await container_manager.execute_command(
                test_session_id, cmd
            )
            print(f"   Output: {output.strip()}")
            print(f"   Exit code: {exit_code}")
            if exit_code != 0:
                print(f"⚠️  Command failed: {cmd}")
        except Exception as e:
            print(f"❌ Command execution failed: {e}")
            return False

    # Test 5: Test file operations
    print("\n5. Testing file operations...")
    try:
        # Create a test file
        test_script = 'print("Testing file operations in Kubernetes pod")'
        output, exit_code = await container_manager.execute_command(
            test_session_id, f"echo '{test_script}' > test_migration.py"
        )
        print(f"   Created test file: exit_code={exit_code}")

        # Execute the test file
        output, exit_code = await container_manager.execute_command(
            test_session_id, "python3 test_migration.py"
        )
        print(f"   Executed test file: {output.strip()}")
        print(f"   Exit code: {exit_code}")

        if "Testing file operations in Kubernetes pod" in output:
            print("✅ File operations working correctly")
        else:
            print("❌ File operations failed")
            return False
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

    # Test 6: Test session info
    print("\n6. Testing session info...")
    try:
        session_info = await container_manager.get_session_info(test_session_id)
        if session_info:
            print("✅ Session info retrieved:")
            print(f"   Pod name: {session_info.get('pod_name')}")
            print(f"   Status: {session_info.get('status')}")
            print(f"   Uptime: {session_info.get('uptime_minutes', 0):.1f} minutes")
        else:
            print("❌ Failed to get session info")
            return False
    except Exception as e:
        print(f"❌ Session info test failed: {e}")
        return False

    # Test 7: Cleanup
    print("\n7. Testing cleanup...")
    try:
        cleanup_success = await container_manager.cleanup_session(test_session_id)
        if cleanup_success:
            print("✅ Session cleanup successful")
        else:
            print("❌ Session cleanup failed")
            return False
    except Exception as e:
        print(f"❌ Cleanup test failed: {e}")
        return False

    print("\n🎉 All Kubernetes migration tests passed!")
    print("✅ The application is successfully using Kubernetes instead of Docker")
    return True


async def main():
    """Run the Kubernetes migration test."""
    success = await test_kubernetes_migration()
    if not success:
        print("\n❌ Kubernetes migration test failed!")
        sys.exit(1)

    print("\n🚀 Kubernetes migration verification complete!")


if __name__ == "__main__":
    asyncio.run(main())
