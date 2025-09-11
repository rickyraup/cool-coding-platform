-- users.sql

CREATE TABLE users (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY
    CONSTRAINT users_pkey,
  username VARCHAR(255) NOT NULL
    CONSTRAINT users_username_unique UNIQUE,
  email VARCHAR(255) NOT NULL
    CONSTRAINT users_email_unique UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
