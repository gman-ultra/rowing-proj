-- Migration: 002_add_concept2_integrations
-- Creates oauth_states and concept2_connections tables for
-- Concept2 OAuth integration.
--
-- Idempotent: safe to run multiple times.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables WHERE table_name = 'oauth_states'
  ) THEN
    CREATE TABLE oauth_states (
      id UUID NOT NULL DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id),
      provider VARCHAR(50) NOT NULL,
      state VARCHAR(255) NOT NULL UNIQUE,
      redirect_after VARCHAR(500),
      expires_at TIMESTAMP NOT NULL,
      consumed_at TIMESTAMP,
      created_at TIMESTAMP NOT NULL DEFAULT NOW(),
      PRIMARY KEY (id)
    );
    CREATE INDEX idx_oauth_states_state ON oauth_states(state);
    CREATE INDEX idx_oauth_states_user_id ON oauth_states(user_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables WHERE table_name = 'concept2_connections'
  ) THEN
    CREATE TABLE concept2_connections (
      id UUID NOT NULL DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL UNIQUE REFERENCES users(id),
      concept2_user_id VARCHAR(255),
      access_token_encrypted TEXT NOT NULL,
      refresh_token_encrypted TEXT,
      token_expires_at TIMESTAMP,
      scope VARCHAR(255),
      last_sync_at TIMESTAMP,
      created_at TIMESTAMP NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
      PRIMARY KEY (id)
    );
    CREATE INDEX idx_concept2_connections_user_id ON concept2_connections(user_id);
  END IF;
END $$;
