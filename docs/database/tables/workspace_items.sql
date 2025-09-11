CREATE TABLE code_editor_project.workspace_items (
  id BIGINT GENERATED ALWAYS AS IDENTITY,
  session_id BIGINT NOT NULL,
  parent_id BIGINT NULL,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(10) NOT NULL,
  content TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT workspace_items_pkey PRIMARY KEY (id),
  CONSTRAINT workspace_items_session_id_fkey FOREIGN KEY (session_id)
    REFERENCES code_editor_project.sessions(id) ON DELETE CASCADE,
  CONSTRAINT workspace_items_parent_id_fkey FOREIGN KEY (parent_id)
    REFERENCES code_editor_project.workspace_items(id) ON DELETE CASCADE,
  CONSTRAINT workspace_items_type_check CHECK (type IN ('file', 'folder'))
);

-- Composite index to speed up lookups by session and parent folder
CREATE INDEX idx_workspace_items_session_parent
  ON code_editor_project.workspace_items (session_id, parent_id);
