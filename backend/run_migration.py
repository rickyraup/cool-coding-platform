#!/usr/bin/env python3
"""Run database migration script."""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.postgres import get_db


def run_migration(migration_file: str) -> None:
    """Run a SQL migration file."""
    migration_path = Path(__file__).parent / "migrations" / migration_file
    
    if not migration_path.exists():
        print(f"Migration file not found: {migration_path}")
        return
    
    print(f"Running migration: {migration_file}")
    
    try:
        with open(migration_path, 'r') as f:
            sql_content = f.read()
        
        db = get_db()
        
        # Handle PostgreSQL functions with dollar-quoted strings properly
        # Don't split on semicolons inside $$ blocks
        statements = []
        current_statement = ""
        in_dollar_quote = False
        dollar_tag = None
        
        lines = sql_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('--'):
                continue
                
            # Check for dollar quote start/end
            if '$$' in line and not in_dollar_quote:
                # Starting a dollar quote
                in_dollar_quote = True
                dollar_tag = '$$'
                current_statement += line + '\n'
            elif in_dollar_quote and dollar_tag in line:
                # Ending a dollar quote
                in_dollar_quote = False
                dollar_tag = None
                current_statement += line + '\n'
            elif in_dollar_quote:
                # Inside dollar quote, just add the line
                current_statement += line + '\n'
            else:
                # Regular SQL line
                current_statement += line + '\n'
                if line.endswith(';'):
                    # End of statement
                    statements.append(current_statement.strip())
                    current_statement = ""
        
        # Add any remaining statement
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        # Filter out empty statements
        statements = [stmt for stmt in statements if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement.strip():
                print(f"Executing statement {i}/{len(statements)}")
                try:
                    db.execute_raw(statement)
                    print(f"✅ Statement {i} executed successfully")
                except Exception as e:
                    print(f"❌ Error in statement {i}: {e}")
                    print(f"Statement: {statement[:100]}...")
                    raise
        
        print(f"✅ Migration {migration_file} completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_migration.py <migration_file>")
        print("Example: python run_migration.py 002_add_review_system.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    run_migration(migration_file)