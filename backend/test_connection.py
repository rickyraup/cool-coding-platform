#!/usr/bin/env python3
"""Test PostgreSQL connection to Supabase"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Test different connection formats
urls_to_test = [
    # Try with SSL
    "postgresql://postgres.dbwplldqbkoahbghmmme:R1ckster10!@aws-1-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require",
    # Try with different user format - just postgres
    "postgresql://postgres:R1ckster10!@aws-1-us-east-2.pooler.supabase.com:6543/postgres",
    # Try with SSL and postgres user
    "postgresql://postgres:R1ckster10!@aws-1-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require",
    # Original format
    "postgresql://postgres.dbwplldqbkoahbghmmme:R1ckster10!@aws-1-us-east-2.pooler.supabase.com:6543/postgres",
    # Current env var
    os.getenv("DATABASE_URL")
]

for i, url in enumerate(urls_to_test):
    if not url:
        continue
    print(f"\n=== Testing connection {i+1}: {url[:50]}... ===")
    try:
        conn = psycopg2.connect(url)
        cursor = conn.cursor()
        cursor.execute("SELECT NOW()")
        result = cursor.fetchone()
        print(f"✅ SUCCESS: Connected! Current time: {result[0]}")
        
        # Test basic query
        cursor.execute("SELECT current_database(), current_user")
        result = cursor.fetchone()
        print(f"✅ Database: {result[0]}, User: {result[1]}")
        
        cursor.close()
        conn.close()
        
        print(f"✅ This connection works! URL: {url}")
        break
        
    except Exception as e:
        print(f"❌ FAILED: {e}")

print("\n=== Connection test complete ===")