#!/usr/bin/env python3
"""Run UUID migration for sessions security."""

from app.core.postgres import get_db

def run_migration():
    """Execute the UUID migration."""
    db = get_db()
    
    print("🔧 Running UUID migration...")
    
    try:
        # Step 1: Add UUID column to sessions table
        print("📝 Step 1: Adding UUID column to sessions table")
        db.execute_raw("""
            ALTER TABLE code_editor_project.sessions 
            ADD COLUMN uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL
        """, ())
        print("   ✅ UUID column added")
        
        # Step 2: Create index on UUID
        print("📝 Step 2: Creating index on UUID")
        db.execute_raw("""
            CREATE INDEX idx_sessions_uuid ON code_editor_project.sessions(uuid)
        """, ())
        print("   ✅ Index created")
        
        # Step 3: Update existing sessions (should be automatically handled by DEFAULT)
        print("📝 Step 3: Verifying existing sessions have UUIDs")
        result = db.execute_query("""
            SELECT COUNT(*) as count FROM code_editor_project.sessions WHERE uuid IS NULL
        """, ())
        null_count = result[0]['count'] if result else 0
        print(f"   ✅ Sessions without UUID: {null_count}")
        
        # Step 4: Add session_uuid to workspace_items
        print("📝 Step 4: Adding session_uuid to workspace_items")
        db.execute_raw("""
            ALTER TABLE code_editor_project.workspace_items 
            ADD COLUMN session_uuid UUID
        """, ())
        print("   ✅ session_uuid column added")
        
        # Step 5: Populate session_uuid in workspace_items
        print("📝 Step 5: Populating session_uuid in workspace_items")
        db.execute_update("""
            UPDATE code_editor_project.workspace_items 
            SET session_uuid = (
                SELECT uuid 
                FROM code_editor_project.sessions 
                WHERE sessions.id = workspace_items.session_id
            )
        """, ())
        print("   ✅ session_uuid populated")
        
        # Step 6: Make session_uuid NOT NULL
        print("📝 Step 6: Making session_uuid NOT NULL")
        db.execute_raw("""
            ALTER TABLE code_editor_project.workspace_items 
            ALTER COLUMN session_uuid SET NOT NULL
        """, ())
        print("   ✅ session_uuid set to NOT NULL")
        
        # Step 7: Create index on session_uuid
        print("📝 Step 7: Creating index on session_uuid")
        db.execute_raw("""
            CREATE INDEX idx_workspace_items_session_uuid 
            ON code_editor_project.workspace_items(session_uuid)
        """, ())
        print("   ✅ Index created")
        
        print("🎉 Migration completed successfully!")
        
        # Show some sample UUIDs
        print("\n📊 Sample session UUIDs:")
        sessions = db.execute_query("""
            SELECT id, uuid, name 
            FROM code_editor_project.sessions 
            ORDER BY created_at DESC 
            LIMIT 5
        """, ())
        for session in sessions:
            print(f"   Session {session['id']}: {session['uuid']} ({session['name'] or 'Unnamed'})")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()