-- Raw Immutable Events table.
CREATE TABLE IF NOT EXISTS raw_events (
    id                  BIGSERIAL PRIMARY KEY,
    event_id            UUID NOT NULL UNIQUE,
    user_id             TEXT NOT NULL,
    session_id          TEXT,
    category            TEXT NOT NULL,
    schema_version      TEXT NOT NULL,
    subject_scope       TEXT NOT NULL DEFAULT 'user',
    surface             TEXT NOT NULL DEFAULT 'unknown',
    locale              TEXT NOT NULL DEFAULT 'und',
    occurred_at         TIMESTAMPTZ NOT NULL,
    received_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    consent_state       TEXT NOT NULL DEFAULT 'pending',
    source_event_id     TEXT,
    idempotency_key     TEXT NOT NULL,
    payload             JSONB NOT NULL,
    client_metadata     JSONB NOT NULL DEFAULT '{}',
    is_important        BOOLEAN,
    importance_score    DOUBLE PRECISION,
    processed_at        TIMESTAMPTZ
);

-- A retry may have a new transport event id; its idempotency key still makes
-- raw-event ingestion exactly-once per user.
CREATE UNIQUE INDEX IF NOT EXISTS raw_events_user_idempotency_key
    ON raw_events (user_id, idempotency_key);

CREATE INDEX IF NOT EXISTS idx_raw_events_user_id ON raw_events (user_id);
CREATE INDEX IF NOT EXISTS idx_raw_events_category ON raw_events (category);
CREATE INDEX IF NOT EXISTS idx_raw_events_occurred_at ON raw_events (occurred_at);
