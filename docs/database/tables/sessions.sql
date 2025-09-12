CREATE TABLE code_editor_project.sessions (
  id BIGINT GENERATED ALWAYS AS IDENTITY,
  user_id BIGINT NOT NULL,
  name VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT sessions_pkey PRIMARY KEY (id),
  CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES code_editor_project.users(id) ON DELETE CASCADE
);
