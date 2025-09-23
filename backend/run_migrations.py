#!/usr/bin/env python3
"""
Run database migrations against Supabase PostgreSQL database.
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable is required")
    sys.exit(1)

def run_migration(file_path: Path) -> bool:
    """Run a single migration file."""
    try:
        print(f"🔄 Running migration: {file_path.name}")
        
        # Read the SQL file
        with open(file_path, 'r') as f:
            sql_content = f.read()
        
        # Connect to database and execute
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            cursor.execute(sql_content)
        
        conn.close()
        print(f"✅ Completed migration: {file_path.name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed migration {file_path.name}: {str(e)}")
        return False

def main():
    """Run all migrations in order."""
    migrations_dir = Path(__file__).parent / "migrations"
    
    # Migration files in order
    migration_files = [
        "001_create_all_tables.sql",
        "002_add_review_system_safe.sql", 
        "003_add_code_to_sessions.sql"
    ]
    
    print("🚀 Starting database migrations...")
    print(f"📍 Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Unknown'}")
    
    success_count = 0
    for filename in migration_files:
        file_path = migrations_dir / filename
        if file_path.exists():
            if run_migration(file_path):
                success_count += 1
        else:
            print(f"⚠️ Migration file not found: {filename}")
    
    print(f"\n🎉 Completed {success_count}/{len(migration_files)} migrations successfully!")
    
    if success_count == len(migration_files):
        print("✅ All migrations completed successfully!")
    else:
        print("❌ Some migrations failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()