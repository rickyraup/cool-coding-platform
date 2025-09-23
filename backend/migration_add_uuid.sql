-- Migration: Add UUID field to sessions table for security
-- This adds a public-facing UUID while keeping the sequential ID as internal primary key

-- Add UUID column to sessions table
ALTER TABLE code_editor_project.sessions 
ADD COLUMN uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL;

-- Create index on UUID for fast lookups
CREATE INDEX idx_sessions_uuid ON code_editor_project.sessions(uuid);

-- Update existing sessions to have UUIDs (if any exist)
UPDATE code_editor_project.sessions 
SET uuid = gen_random_uuid() 
WHERE uuid IS NULL;

-- Add UUID column to workspace_items table and reference session by UUID
ALTER TABLE code_editor_project.workspace_items 
ADD COLUMN session_uuid UUID;

-- Update workspace_items to reference session UUIDs
UPDATE code_editor_project.workspace_items 
SET session_uuid = (
    SELECT uuid 
    FROM code_editor_project.sessions 
    WHERE sessions.id = workspace_items.session_id
);

-- Make session_uuid NOT NULL after population
ALTER TABLE code_editor_project.workspace_items 
ALTER COLUMN session_uuid SET NOT NULL;

-- Create index on session_uuid for fast lookups  
CREATE INDEX idx_workspace_items_session_uuid ON code_editor_project.workspace_items(session_uuid);

-- Add UUID column to reviews table if it exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'code_editor_project' AND table_name = 'reviews') THEN
        ALTER TABLE code_editor_project.reviews ADD COLUMN session_uuid UUID;
        
        UPDATE code_editor_project.reviews 
        SET session_uuid = (
            SELECT uuid 
            FROM code_editor_project.sessions 
            WHERE sessions.id = reviews.session_id
        );
        
        ALTER TABLE code_editor_project.reviews 
        ALTER COLUMN session_uuid SET NOT NULL;
        
        CREATE INDEX idx_reviews_session_uuid ON code_editor_project.reviews(session_uuid);
    END IF;
END $$;

COMMIT;