"""Test PostgreSQL connection to Supabase."""

import os
import sys
import traceback
from typing import Optional

from app.core.postgres import get_db, init_db


def test_connection() -> Optional[bool]:
    """Test the PostgreSQL connection."""
    try:
        print("🔄 Testing PostgreSQL connection to Supabase...")

        # Debug: Show parsed connection parameters
        db = get_db()
        print("📋 Connection parameters:")
        print(f"   Host: {db.connection_params['host']}")
        print(f"   Port: {db.connection_params['port']}")
        print(f"   Database: {db.connection_params['database']}")
        print(f"   User: {db.connection_params['user']}")
        print(f"   Password: {'*' * len(str(db.connection_params['password']) or '')}")

        init_db()

        # Test a simple query
        db = get_db()
        result = db.execute_one("SELECT NOW() as current_time")
        print(f"✅ Query test successful! Current time: {result['current_time']}")

        # Test if our schema exists
        schema_check = db.execute_one("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = 'code_editor_project'
        """)

        if schema_check:
            print("✅ Schema 'code_editor_project' exists")

            # Check if tables exist
            tables_check = db.execute_query("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'code_editor_project'
                ORDER BY table_name
            """)

            if tables_check:
                print(f"✅ Found {len(tables_check)} tables:")
                for table in tables_check:
                    print(f"   - {table['table_name']}")
            else:
                print("⚠️ No tables found in schema")
        else:
            print("❌ Schema 'code_editor_project' does not exist")
            return False

        return True

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("PostgreSQL Connection Test")
    print("=" * 40)

    # Check if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    if not db_url or "[YOUR-PASSWORD]" in db_url:
        print("❌ Please set your DATABASE_URL with the actual password in .env file")
        print("   Current DATABASE_URL:", db_url)
        sys.exit(1)

    success = test_connection()

    if success:
        print("\n✅ All tests passed! PostgreSQL connection is ready.")
    else:
        print("\n❌ Connection test failed. Please check your configuration.")
        sys.exit(1)
