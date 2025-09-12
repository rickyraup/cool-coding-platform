CREATE TABLE code_editor_project.users (
  id BIGINT GENERATED ALWAYS AS IDENTITY,
  username VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT users_pkey PRIMARY KEY (id),
  CONSTRAINT users_username_unique UNIQUE (username),
  CONSTRAINT users_email_unique UNIQUE (email)
);
