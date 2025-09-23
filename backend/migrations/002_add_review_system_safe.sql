-- Migration: Add Review System Tables (Safe Version)
-- Description: Add tables for workspace review and approval workflow with existence checks

-- Add reviewer role to users table (safe)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='code_editor_project' AND table_name='users' AND column_name='is_reviewer') THEN
        ALTER TABLE code_editor_project.users ADD COLUMN is_reviewer BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='code_editor_project' AND table_name='users' AND column_name='reviewer_level') THEN
        ALTER TABLE code_editor_project.users ADD COLUMN reviewer_level INTEGER DEFAULT 0;
    END IF;
END $$;

-- Create review requests table
CREATE TABLE IF NOT EXISTS code_editor_project.review_requests (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES code_editor_project.sessions(id) ON DELETE CASCADE,
    submitted_by INTEGER NOT NULL REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    assigned_to INTEGER REFERENCES code_editor_project.users(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'in_review', 'approved', 'rejected', 'requires_changes')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    submitted_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create review comments table
CREATE TABLE IF NOT EXISTS code_editor_project.review_comments (
    id SERIAL PRIMARY KEY,
    review_request_id INTEGER NOT NULL REFERENCES code_editor_project.review_requests(id) ON DELETE CASCADE,
    commenter_id INTEGER NOT NULL REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    workspace_item_id INTEGER REFERENCES code_editor_project.workspace_items(id) ON DELETE SET NULL,
    line_number INTEGER,
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(50) DEFAULT 'general' CHECK (comment_type IN ('general', 'suggestion', 'issue', 'question', 'approval')),
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create review history table for audit trail
CREATE TABLE IF NOT EXISTS code_editor_project.review_history (
    id SERIAL PRIMARY KEY,
    review_request_id INTEGER NOT NULL REFERENCES code_editor_project.review_requests(id) ON DELETE CASCADE,
    changed_by INTEGER NOT NULL REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    change_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create review assignments table (for multiple reviewers)
CREATE TABLE IF NOT EXISTS code_editor_project.review_assignments (
    id SERIAL PRIMARY KEY,
    review_request_id INTEGER NOT NULL REFERENCES code_editor_project.review_requests(id) ON DELETE CASCADE,
    reviewer_id INTEGER NOT NULL REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER REFERENCES code_editor_project.users(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'assigned' CHECK (status IN ('assigned', 'accepted', 'declined', 'completed')),
    UNIQUE(review_request_id, reviewer_id)
);

-- Add indexes for performance (safe)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='code_editor_project' AND tablename='review_requests' AND indexname='idx_review_requests_status') THEN
        CREATE INDEX idx_review_requests_status ON code_editor_project.review_requests(status);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='code_editor_project' AND tablename='review_requests' AND indexname='idx_review_requests_submitted_by') THEN
        CREATE INDEX idx_review_requests_submitted_by ON code_editor_project.review_requests(submitted_by);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='code_editor_project' AND tablename='review_requests' AND indexname='idx_review_requests_assigned_to') THEN
        CREATE INDEX idx_review_requests_assigned_to ON code_editor_project.review_requests(assigned_to);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='code_editor_project' AND tablename='review_comments' AND indexname='idx_review_comments_review_request') THEN
        CREATE INDEX idx_review_comments_review_request ON code_editor_project.review_comments(review_request_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='code_editor_project' AND tablename='review_assignments' AND indexname='idx_review_assignments_reviewer') THEN
        CREATE INDEX idx_review_assignments_reviewer ON code_editor_project.review_assignments(reviewer_id);
    END IF;
END $$;

-- Create trigger function for updating review_requests.updated_at
CREATE OR REPLACE FUNCTION update_review_requests_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger (safe)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='trigger_review_requests_updated_at') THEN
        CREATE TRIGGER trigger_review_requests_updated_at
            BEFORE UPDATE ON code_editor_project.review_requests
            FOR EACH ROW
            EXECUTE FUNCTION update_review_requests_updated_at();
    END IF;
END $$;

-- Create trigger function for review history logging
CREATE OR REPLACE FUNCTION log_review_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO code_editor_project.review_history (
            review_request_id, 
            changed_by, 
            old_status, 
            new_status,
            change_description
        ) VALUES (
            NEW.id,
            NEW.assigned_to,
            OLD.status,
            NEW.status,
            CASE 
                WHEN NEW.status = 'approved' THEN 'Review approved'
                WHEN NEW.status = 'rejected' THEN 'Review rejected'
                WHEN NEW.status = 'requires_changes' THEN 'Changes requested'
                WHEN NEW.status = 'in_review' THEN 'Review started'
                ELSE 'Status updated'
            END
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for logging (safe)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='trigger_log_review_status_change') THEN
        CREATE TRIGGER trigger_log_review_status_change
            AFTER UPDATE ON code_editor_project.review_requests
            FOR EACH ROW
            EXECUTE FUNCTION log_review_status_change();
    END IF;
END $$;