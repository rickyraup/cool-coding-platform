-- Migration: Add code storage to sessions table
-- This adds the ability to store and save code content in sessions

-- Add code column to sessions table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'code_editor_project'
        AND table_name = 'sessions' 
        AND column_name = 'code'
    ) THEN
        ALTER TABLE code_editor_project.sessions ADD COLUMN code TEXT DEFAULT '# Write your Python code here\nprint("Hello, World!")';
        RAISE NOTICE 'Added code column to sessions table';
    ELSE
        RAISE NOTICE 'Code column already exists in sessions table';
    END IF;
END $$;

-- Add language column to sessions table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'code_editor_project'
        AND table_name = 'sessions' 
        AND column_name = 'language'
    ) THEN
        ALTER TABLE code_editor_project.sessions ADD COLUMN language VARCHAR(50) DEFAULT 'python';
        RAISE NOTICE 'Added language column to sessions table';
    ELSE
        RAISE NOTICE 'Language column already exists in sessions table';
    END IF;
END $$;

-- Add is_active column to sessions table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'code_editor_project'
        AND table_name = 'sessions' 
        AND column_name = 'is_active'
    ) THEN
        ALTER TABLE code_editor_project.sessions ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
        RAISE NOTICE 'Added is_active column to sessions table';
    ELSE
        RAISE NOTICE 'Is_active column already exists in sessions table';
    END IF;
END $$;