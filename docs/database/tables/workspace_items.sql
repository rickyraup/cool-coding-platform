-- 003_create_workspace_items.sql

CREATE TABLE workspace_items (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY
    CONSTRAINT workspace_items_pkey,
  session_id BIGINT NOT NULL
    CONSTRAINT workspace_items_session_id_fkey REFERENCES sessions(id) ON DELETE CASCADE,
  parent_id BIGINT NULL
    CONSTRAINT workspace_items_parent_id_fkey REFERENCES workspace_items(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(10) NOT NULL
    CONSTRAINT workspace_items_type_check CHECK (type IN ('file', 'folder')),
  content TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_workspace_items_session_parent
  ON workspace_items (session_id, parent_id);
