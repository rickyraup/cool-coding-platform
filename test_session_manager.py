#!/usr/bin/env python3
"""Test script for the session manager."""

import asyncio
import sys
import os

# Add the backend app to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.core.session_manager import session_manager

async def test_session_manager():
    print("🧪 Testing Session Manager...")
    
    # Create a test session
    session_id = "test-session-123"
    print(f"📝 Creating session: {session_id}")
    
    try:
        # Test basic commands
        commands_to_test = [
            "echo 'Hello, isolated terminal!'",
            "pwd",
            "ps",
            "ls -la",
            "whoami",
            "echo $HOME",
            "python3 -c 'import os; print(f\"Python PID: {os.getpid()}\")'",
            "mkdir test_dir",
            "ls -la",
            "touch test_file.txt",
            "ls -la",
        ]
        
        for cmd in commands_to_test:
            print(f"\n🏃 Executing: {cmd}")
            output, return_code = await session_manager.execute_command(session_id, cmd)
            print(f"📤 Output (return_code={return_code}):")
            print(output)
            print("-" * 50)
            
        # Check session info
        print("\n📊 Session info:")
        session_info = session_manager.get_session_info(session_id)
        print(session_info)
        
        # List all sessions
        print("\n📋 All active sessions:")
        all_sessions = session_manager.list_sessions()
        print(all_sessions)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        
    finally:
        # Clean up
        print(f"\n🧹 Cleaning up session: {session_id}")
        await session_manager.cleanup_session(session_id)
        print("✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_session_manager())