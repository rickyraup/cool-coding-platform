CREATE TABLE code_editor_project.users (
  id BIGINT GENERATED ALWAYS AS IDENTITY,
  username VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_reviewer BOOLEAN DEFAULT FALSE,
  reviewer_level INTEGER DEFAULT 0 CHECK (reviewer_level >= 0 AND reviewer_level <= 2),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT users_pkey PRIMARY KEY (id),
  CONSTRAINT users_username_unique UNIQUE (username),
  CONSTRAINT users_email_unique UNIQUE (email)
);

-- Comments for reviewer fields:
-- is_reviewer: Whether the user can review code submissions
-- reviewer_level: 0=regular user, 1=junior reviewer, 2=senior reviewer
