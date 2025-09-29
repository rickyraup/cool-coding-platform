#!/usr/bin/env python3
"""
Test script to monitor Docker container cleanup when navigating away from workspace.

Usage:
1. Run this script in one terminal: python test_container_cleanup.py
2. In your browser, navigate to a workspace
3. Hit the back arrow to go to dashboard
4. Check the script output to see if containers were cleaned up
"""

import time
import subprocess
import json
from datetime import datetime

def get_coding_containers():
    """Get list of coding session containers."""
    try:
        result = subprocess.run([
            'docker', 'ps',
            '--filter', 'name=coding-session',
            '--format', 'json'
        ], capture_output=True, text=True, check=True)

        containers = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                containers.append(json.loads(line))
        return containers
    except subprocess.CalledProcessError:
        return []

def print_containers(containers, label):
    """Print container information."""
    print(f"\n🐳 {label}")
    print("=" * 50)
    if not containers:
        print("No coding session containers found")
    else:
        for container in containers:
            print(f"Container: {container['Names']}")
            print(f"Status: {container['Status']}")
            print(f"Image: {container['Image']}")
            print(f"Created: {container['CreatedAt']}")
            print("-" * 30)

def monitor_containers():
    """Monitor containers continuously."""
    print("🔍 Docker Container Cleanup Monitor")
    print("=" * 50)
    print("Instructions:")
    print("1. Open your browser and navigate to a workspace")
    print("2. Use the terminal or editor to create some activity")
    print("3. Hit the back arrow to return to dashboard")
    print("4. Watch this monitor for container cleanup")
    print("5. Press Ctrl+C to stop monitoring")
    print("=" * 50)

    previous_containers = []

    try:
        while True:
            current_containers = get_coding_containers()

            # Check for new containers
            current_names = {c['Names'] for c in current_containers}
            previous_names = {c['Names'] for c in previous_containers}

            new_containers = current_names - previous_names
            removed_containers = previous_names - current_names

            if new_containers:
                print(f"\n✅ [{datetime.now().strftime('%H:%M:%S')}] NEW CONTAINER(S) CREATED:")
                for name in new_containers:
                    print(f"   📦 {name}")

            if removed_containers:
                print(f"\n🧹 [{datetime.now().strftime('%H:%M:%S')}] CONTAINER(S) CLEANED UP:")
                for name in removed_containers:
                    print(f"   🗑️  {name}")
                print("   ✅ Container cleanup successful!")

            # Show current state every 10 seconds or when changes occur
            if new_containers or removed_containers or len(current_containers) > 0:
                print(f"\n📊 [{datetime.now().strftime('%H:%M:%S')}] Current containers: {len(current_containers)}")
                for container in current_containers:
                    print(f"   🏃 {container['Names']} - {container['Status']}")

            previous_containers = current_containers
            time.sleep(2)  # Check every 2 seconds

    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped. Final container check:")
        final_containers = get_coding_containers()
        print_containers(final_containers, "Final Container State")

if __name__ == "__main__":
    monitor_containers()