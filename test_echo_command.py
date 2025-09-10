#!/usr/bin/env python3
"""Test the echo command specifically."""

import asyncio
import sys
import os

# Add the backend app to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.core.session_manager import session_manager

async def test_echo_command():
    print("🧪 Testing Echo Command...")
    
    session_id = "test-echo-session"
    
    try:
        # Test the problematic echo command
        print("🏃 Executing: echo bro")
        output, return_code = await session_manager.execute_command(session_id, "echo bro")
        print(f"📤 Raw output (return_code={return_code}):")
        print(f"'{output}'")
        print(f"📏 Output length: {len(output)} characters")
        
        # Test another simple command
        print("\n🏃 Executing: echo 'Hello World'")
        output, return_code = await session_manager.execute_command(session_id, "echo 'Hello World'")
        print(f"📤 Raw output (return_code={return_code}):")
        print(f"'{output}'")
        
        # Test with variables
        print("\n🏃 Executing: echo $USER")
        output, return_code = await session_manager.execute_command(session_id, "echo $USER")
        print(f"📤 Raw output (return_code={return_code}):")
        print(f"'{output}'")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        
    finally:
        # Clean up
        print(f"\n🧹 Cleaning up session: {session_id}")
        await session_manager.cleanup_session(session_id)
        print("✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_echo_command())