-- Migration: Add Review System Tables
-- Description: Add tables for workspace review and approval workflow

-- Add reviewer role to users table
ALTER TABLE code_editor_project.users 
ADD COLUMN is_reviewer BOOLEAN DEFAULT FALSE,
ADD COLUMN reviewer_level INTEGER DEFAULT 0; -- 0=regular, 1=junior reviewer, 2=senior reviewer

-- Create review requests table
CREATE TABLE code_editor_project.review_requests (
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
CREATE TABLE code_editor_project.review_comments (
    id SERIAL PRIMARY KEY,
    review_request_id INTEGER NOT NULL REFERENCES code_editor_project.review_requests(id) ON DELETE CASCADE,
    commenter_id INTEGER NOT NULL REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    workspace_item_id INTEGER REFERENCES code_editor_project.workspace_items(id) ON DELETE SET NULL,
    line_number INTEGER, -- For line-specific comments
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(50) DEFAULT 'general' CHECK (comment_type IN ('general', 'suggestion', 'issue', 'question', 'approval')),
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create review history table for audit trail
CREATE TABLE code_editor_project.review_history (
    id SERIAL PRIMARY KEY,
    review_request_id INTEGER NOT NULL REFERENCES code_editor_project.review_requests(id) ON DELETE CASCADE,
    changed_by INTEGER NOT NULL REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    change_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create review assignments table (for multiple reviewers)
CREATE TABLE code_editor_project.review_assignments (
    id SERIAL PRIMARY KEY,
    review_request_id INTEGER NOT NULL REFERENCES code_editor_project.review_requests(id) ON DELETE CASCADE,
    reviewer_id INTEGER NOT NULL REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER REFERENCES code_editor_project.users(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'assigned' CHECK (status IN ('assigned', 'accepted', 'declined', 'completed')),
    UNIQUE(review_request_id, reviewer_id)
);

-- Add indexes for performance
CREATE INDEX idx_review_requests_status ON code_editor_project.review_requests(status);
CREATE INDEX idx_review_requests_submitted_by ON code_editor_project.review_requests(submitted_by);
CREATE INDEX idx_review_requests_assigned_to ON code_editor_project.review_requests(assigned_to);
CREATE INDEX idx_review_comments_review_request ON code_editor_project.review_comments(review_request_id);
CREATE INDEX idx_review_assignments_reviewer ON code_editor_project.review_assignments(reviewer_id);

-- Create trigger for updating review_requests.updated_at
CREATE OR REPLACE FUNCTION update_review_requests_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_review_requests_updated_at
    BEFORE UPDATE ON code_editor_project.review_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_review_requests_updated_at();

-- Create trigger for review history logging
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
            NEW.assigned_to, -- Assuming the assigned reviewer made the change
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

CREATE TRIGGER trigger_log_review_status_change
    AFTER UPDATE ON code_editor_project.review_requests
    FOR EACH ROW
    EXECUTE FUNCTION log_review_status_change();

-- Insert some sample reviewers (update existing users)
UPDATE code_editor_project.users 
SET is_reviewer = TRUE, reviewer_level = 2 
WHERE username IN ('admin', 'reviewer'); -- Adjust based on your existing users

-- Add some comments to the schema
COMMENT ON TABLE code_editor_project.review_requests IS 'Stores workspace review requests and their status';
COMMENT ON TABLE code_editor_project.review_comments IS 'Stores reviewer comments on code and files';
COMMENT ON TABLE code_editor_project.review_history IS 'Audit trail for review status changes';
COMMENT ON TABLE code_editor_project.review_assignments IS 'Tracks multiple reviewer assignments per request';

COMMENT ON COLUMN code_editor_project.users.is_reviewer IS 'Whether user can review other users'' workspaces';
COMMENT ON COLUMN code_editor_project.users.reviewer_level IS '0=regular, 1=junior reviewer, 2=senior reviewer';