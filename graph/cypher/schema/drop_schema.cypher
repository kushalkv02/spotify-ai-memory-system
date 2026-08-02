// ============================================================
// Drops every constraint/index created above.
// Useful while iterating on the schema during early development.
// Run with: python -m graph.builders.graph_builder --drop
// ============================================================

DROP CONSTRAINT user_id_unique IF EXISTS;
DROP CONSTRAINT track_id_unique IF EXISTS;
DROP CONSTRAINT artist_id_unique IF EXISTS;
DROP CONSTRAINT album_id_unique IF EXISTS;
DROP CONSTRAINT playlist_id_unique IF EXISTS;
DROP CONSTRAINT session_id_unique IF EXISTS;
DROP CONSTRAINT memory_id_unique IF EXISTS;
DROP CONSTRAINT preference_id_unique IF EXISTS;
DROP CONSTRAINT conversation_id_unique IF EXISTS;
DROP CONSTRAINT message_id_unique IF EXISTS;

DROP INDEX track_title_idx IF EXISTS;
DROP INDEX artist_name_idx IF EXISTS;
DROP INDEX user_email_idx IF EXISTS;
DROP INDEX memory_created_at_idx IF EXISTS;
DROP INDEX session_started_at_idx IF EXISTS;
DROP INDEX played_at_idx IF EXISTS;
DROP INDEX liked_at_idx IF EXISTS;
DROP INDEX skipped_at_idx IF EXISTS;
DROP INDEX followed_at_idx IF EXISTS;
