-- Complete database schema for Code Execution Platform
-- This creates all tables needed including save functionality

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS code_editor_project;

-- Drop tables if they exist (for fresh start)
DROP TABLE IF EXISTS code_editor_project.review_comments CASCADE;
DROP TABLE IF EXISTS code_editor_project.review_history CASCADE;
DROP TABLE IF EXISTS code_editor_project.review_assignments CASCADE;
DROP TABLE IF EXISTS code_editor_project.review_requests CASCADE;
DROP TABLE IF EXISTS code_editor_project.workspace_items CASCADE;
DROP TABLE IF EXISTS code_editor_project.sessions CASCADE;
DROP TABLE IF EXISTS code_editor_project.users CASCADE;

-- Users table
CREATE TABLE code_editor_project.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions table (with code storage for save functionality)
CREATE TABLE code_editor_project.sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    name VARCHAR(255),
    code TEXT DEFAULT '# Write your Python code here
print("Hello, World!")',
    language VARCHAR(50) DEFAULT 'python',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workspace items table
CREATE TABLE code_editor_project.workspace_items (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES code_editor_project.sessions(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES code_editor_project.workspace_items(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(10) CHECK (type IN ('file', 'folder')) NOT NULL,
    content TEXT,
    full_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Review requests table
CREATE TABLE code_editor_project.review_requests (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES code_editor_project.sessions(id) ON DELETE CASCADE,
    submitted_by INTEGER REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    assigned_to INTEGER REFERENCES code_editor_project.users(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_review', 'approved', 'rejected', 'requires_changes')),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Review comments table
CREATE TABLE code_editor_project.review_comments (
    id SERIAL PRIMARY KEY,
    review_request_id INTEGER REFERENCES code_editor_project.review_requests(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    comment TEXT NOT NULL,
    line_number INTEGER,
    file_path VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Review history table
CREATE TABLE code_editor_project.review_history (
    id SERIAL PRIMARY KEY,
    review_request_id INTEGER REFERENCES code_editor_project.review_requests(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Review assignments table
CREATE TABLE code_editor_project.review_assignments (
    id SERIAL PRIMARY KEY,
    review_request_id INTEGER REFERENCES code_editor_project.review_requests(id) ON DELETE CASCADE,
    reviewer_id INTEGER REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    assigned_by INTEGER REFERENCES code_editor_project.users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'assigned' CHECK (status IN ('assigned', 'accepted', 'declined', 'completed')),
    UNIQUE(review_request_id, reviewer_id)
);

-- Create indexes for better performance
CREATE INDEX idx_sessions_user_id ON code_editor_project.sessions(user_id);
CREATE INDEX idx_sessions_updated_at ON code_editor_project.sessions(updated_at);
CREATE INDEX idx_workspace_items_session_id ON code_editor_project.workspace_items(session_id);
CREATE INDEX idx_workspace_items_parent_id ON code_editor_project.workspace_items(parent_id);
CREATE INDEX idx_review_requests_session_id ON code_editor_project.review_requests(session_id);
CREATE INDEX idx_review_requests_submitted_by ON code_editor_project.review_requests(submitted_by);
CREATE INDEX idx_review_requests_assigned_to ON code_editor_project.review_requests(assigned_to);
CREATE INDEX idx_review_requests_status ON code_editor_project.review_requests(status);
CREATE INDEX idx_review_comments_review_request_id ON code_editor_project.review_comments(review_request_id);
CREATE INDEX idx_review_history_review_request_id ON code_editor_project.review_history(review_request_id);

-- Insert sample data for testing
INSERT INTO code_editor_project.users (username, email, password_hash) VALUES 
('testuser', 'test@example.com', '$2b$12$dummy_hash_for_testing'),
('reviewer1', 'reviewer1@example.com', '$2b$12$dummy_hash_for_testing'),
('reviewer2', 'reviewer2@example.com', '$2b$12$dummy_hash_for_testing');

-- Insert sample session with code
INSERT INTO code_editor_project.sessions (user_id, name, code, language, is_active) VALUES 
(1, 'My First Session', '# Welcome to the Code Execution Platform
print("Hello, World!")

# You can write Python code here
def greet(name):
    return f"Hello, {name}!"

print(greet("Claude"))', 'python', true);

-- All tables created successfully with sample data!