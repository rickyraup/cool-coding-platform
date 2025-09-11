#!/usr/bin/env python3
"""Simple Docker connectivity test."""

import docker
import sys

try:
    print("🔍 Testing Docker client connection...")
    
    # Try different connection methods
    client = docker.from_env()
    
    print("✅ Docker client created")
    
    # Test ping
    client.ping()
    print("✅ Docker daemon ping successful")
    
    # Test basic info
    info = client.info()
    print(f"✅ Docker info: {info['ServerVersion']}")
    
    # Test simple container run
    print("🔍 Testing simple container run...")
    result = client.containers.run("alpine:latest", "echo 'Hello from Docker!'", remove=True)
    print(f"✅ Container output: {result.decode().strip()}")
    
    print("🎉 All Docker tests passed!")
    
except Exception as e:
    print(f"❌ Docker test failed: {e}")
    print(f"Error type: {type(e)}")
    sys.exit(1)