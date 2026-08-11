-- Kept separate from raw_events: classifications can be recomputed without
-- rewriting immutable captured input, and only retained rows are retrievable.
CREATE TABLE IF NOT EXISTS memory_decisions (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL REFERENCES raw_events(event_id),
    memory_class TEXT NOT NULL,
    retain_as_memory BOOLEAN NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    policy_class TEXT NOT NULL,
    summary TEXT,
    entities JSONB NOT NULL DEFAULT '{}',
    semantic_key TEXT,
    source_event_ids UUID[] NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS memory_decisions_event_id_idx ON memory_decisions(event_id);
CREATE INDEX IF NOT EXISTS retained_memory_semantic_key_idx
    ON memory_decisions(semantic_key) WHERE retain_as_memory;
