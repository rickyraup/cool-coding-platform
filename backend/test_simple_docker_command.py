#!/usr/bin/env python3
"""Test simple Docker command execution."""

import asyncio
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional

from app.services.container_manager import container_manager


async def test_simple_command() -> Optional[bool]:
    """Test a simple command in Docker."""
    print("🐳 Testing simple Docker command execution...")

    session_id = "test-docker-123"

    try:
        # Test simple echo command
        output, exit_code = await container_manager.execute_command(
            session_id, "echo 'Hello from Docker container!'",
        )
        print(f"✅ Command output: {output}")
        print(f"✅ Exit code: {exit_code}")

        # Test ls command
        output, exit_code = await container_manager.execute_command(
            session_id, "ls -la",
        )
        print(f"✅ ls output: {output}")

        # Test pwd command
        output, exit_code = await container_manager.execute_command(session_id, "pwd")
        print(f"✅ pwd output: {output}")

        # Cleanup
        await container_manager.cleanup_session(session_id)
        print("✅ Session cleaned up")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_simple_command())
    sys.exit(0 if success else 1)
