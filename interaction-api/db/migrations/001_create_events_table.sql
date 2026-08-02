-- Raw Immutable Events table.
CREATE TABLE IF NOT EXISTS raw_events (
    id                  BIGSERIAL PRIMARY KEY,
    event_id            UUID NOT NULL UNIQUE,
    user_id             TEXT NOT NULL,
    session_id          TEXT,
    category            TEXT NOT NULL,
    schema_version      TEXT NOT NULL,
    occurred_at         TIMESTAMPTZ NOT NULL,
    received_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload             JSONB NOT NULL,
    client_metadata     JSONB NOT NULL DEFAULT '{}',
    is_important        BOOLEAN,
    importance_score    DOUBLE PRECISION,
    processed_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_raw_events_user_id ON raw_events (user_id);
CREATE INDEX IF NOT EXISTS idx_raw_events_category ON raw_events (category);
CREATE INDEX IF NOT EXISTS idx_raw_events_occurred_at ON raw_events (occurred_at);
