#!/usr/bin/env python3
"""Script to check if session exists in database."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.postgres_models import CodeSession

def check_session(session_uuid):
    """Check if session exists in database."""
    try:
        session = CodeSession.get_by_uuid(session_uuid)
        if session:
            print(f"✓ Session found in database:")
            print(f"  ID: {session.id}")
            print(f"  UUID: {session.uuid}")
            print(f"  User ID: {session.user_id}")
            print(f"  Name: {session.name}")
            print(f"  Active: {session.is_active}")
            print(f"  Created: {session.created_at}")
            print(f"  Updated: {session.updated_at}")
            return True
        else:
            print(f"✗ Session {session_uuid} not found in database")
            return False
    except Exception as e:
        print(f"✗ Error checking session: {e}")
        return False

if __name__ == "__main__":
    session_uuid = "106f0305-c080-4ba9-a64e-f8a7a102286f"
    check_session(session_uuid)