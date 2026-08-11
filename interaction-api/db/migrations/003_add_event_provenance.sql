-- Upgrade existing raw_events deployments from the v1.0 contract.
ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS subject_scope TEXT NOT NULL DEFAULT 'user';
ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS surface TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS locale TEXT NOT NULL DEFAULT 'und';
ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS consent_state TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS source_event_id TEXT;
ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

UPDATE raw_events
SET idempotency_key = event_id::text
WHERE idempotency_key IS NULL;

ALTER TABLE raw_events ALTER COLUMN idempotency_key SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS raw_events_user_idempotency_key
    ON raw_events (user_id, idempotency_key);
