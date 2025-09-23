#!/usr/bin/env python3
"""Run UUID migration for sessions security."""

import os
from app.core.postgres import get_db

def run_migration():
    """Execute the UUID migration."""
    # Read the migration SQL
    with open('migration_add_uuid.sql', 'r') as f:
        migration_sql = f.read()
    
    # Split into individual statements (removing COMMIT at the end)
    statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and stmt.strip() != 'COMMIT']
    
    db = get_db()
    
    print("🔧 Running UUID migration...")
    
    for i, statement in enumerate(statements, 1):
        if statement.strip():
            try:
                print(f"📝 Executing statement {i}/{len(statements)}")
                print(f"   {statement[:60]}{'...' if len(statement) > 60 else ''}")
                db.execute_query(statement, ())
                print(f"   ✅ Success")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                # Continue with other statements
    
    print("🎉 Migration completed!")

if __name__ == "__main__":
    run_migration()