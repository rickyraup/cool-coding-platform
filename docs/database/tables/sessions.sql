-- sessions.sql

CREATE TABLE sessions (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY
    CONSTRAINT sessions_pkey,
  user_id BIGINT NOT NULL
    CONSTRAINT sessions_user_id_fkey REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
