#!/usr/bin/env python3
"""
Add missing user ID 4 to the database.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable is required")
    sys.exit(1)

def add_user():
    """Add user ID 4 to the database."""
    try:
        print("🔄 Adding missing user ID 4...")
        
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # Check if user 4 already exists
            cursor.execute("SELECT id FROM code_editor_project.users WHERE id = 4")
            existing_user = cursor.fetchone()
            
            if existing_user:
                print("✅ User ID 4 already exists")
                return
            
            # Insert user 4
            cursor.execute("""
                INSERT INTO code_editor_project.users (id, username, email, password_hash) 
                VALUES (4, 'user4', 'user4@example.com', '$2b$12$dummy_hash_for_testing')
                ON CONFLICT (id) DO NOTHING
            """)
            
            # Update sequence to prevent conflicts
            cursor.execute("""
                SELECT setval('code_editor_project.users_id_seq', 
                             COALESCE((SELECT MAX(id) FROM code_editor_project.users), 1) + 1, 
                             false)
            """)
        
        conn.close()
        print("✅ Successfully added user ID 4")
        
    except Exception as e:
        print(f"❌ Failed to add user: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    add_user()