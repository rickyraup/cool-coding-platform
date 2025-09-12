#!/usr/bin/env python3
"""Test the fixed Docker client service."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.docker_client import docker_client_service

def test_docker_connection():
    """Test Docker connection with our fixed service."""
    print("🔍 Testing fixed Docker client service...")
    
    try:
        # Test availability check
        is_available = docker_client_service.is_docker_available()
        print(f"Docker available: {is_available}")
        
        if is_available:
            # Test getting client
            client = docker_client_service.client
            print(f"✅ Docker client created: {client}")
            
            # Test ping
            client.ping()
            print("✅ Docker ping successful")
            
            # Test running a simple container
            result = client.containers.run("alpine:latest", "echo 'Hello from Docker!'", remove=True)
            print(f"✅ Container test: {result.decode().strip()}")
            
            return True
        else:
            print("❌ Docker not available")
            return False
            
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_docker_connection()
    sys.exit(0 if success else 1)