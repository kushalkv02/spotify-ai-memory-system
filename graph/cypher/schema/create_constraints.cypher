// ============================================================
// Uniqueness constraints — one per entity's id property.
// Run with: python -m graph.builders.graph_builder --schema
// ============================================================

CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.user_id IS UNIQUE;

CREATE CONSTRAINT track_id_unique IF NOT EXISTS
FOR (t:Track) REQUIRE t.track_id IS UNIQUE;

CREATE CONSTRAINT artist_id_unique IF NOT EXISTS
FOR (a:Artist) REQUIRE a.artist_id IS UNIQUE;

CREATE CONSTRAINT album_id_unique IF NOT EXISTS
FOR (al:Album) REQUIRE al.album_id IS UNIQUE;

CREATE CONSTRAINT playlist_id_unique IF NOT EXISTS
FOR (p:Playlist) REQUIRE p.playlist_id IS UNIQUE;

CREATE CONSTRAINT session_id_unique IF NOT EXISTS
FOR (s:Session) REQUIRE s.session_id IS UNIQUE;

MATCH (m:Memory)
SET m.version_id = coalesce(m.version_id, m.memory_id),
    m.valid_from = coalesce(m.valid_from, m.created_at),
    m.recorded_at = coalesce(m.recorded_at, m.created_at),
    m.source = coalesce(m.source, 'legacy'),
    m.confidence = coalesce(m.confidence, 1.0),
    m.status = coalesce(m.status, 'active'),
    m.subject_scope = coalesce(m.subject_scope, 'user'),
    m.explicitness = coalesce(m.explicitness, 0.0),
    m.repetition = coalesce(m.repetition, 1),
    m.negative_feedback = coalesce(m.negative_feedback, 0.0),
    m.surface_policy = coalesce(m.surface_policy, 'default');

MATCH ()-[r:HAS_MEMORY|REFERENCES]->()
SET r.valid_from = coalesce(r.valid_from, r.created_at),
    r.recorded_at = coalesce(r.recorded_at, r.created_at),
    r.source = coalesce(r.source, 'legacy'),
    r.confidence = coalesce(r.confidence, 1.0),
    r.status = coalesce(r.status, 'active'),
    r.subject_scope = coalesce(r.subject_scope, 'user');

DROP CONSTRAINT memory_id_unique IF EXISTS;

CREATE CONSTRAINT memory_version_id_unique IF NOT EXISTS
FOR (m:Memory) REQUIRE m.version_id IS UNIQUE;

CREATE CONSTRAINT preference_id_unique IF NOT EXISTS
FOR (p:Preference) REQUIRE p.preference_id IS UNIQUE;

CREATE CONSTRAINT conversation_id_unique IF NOT EXISTS
FOR (c:Conversation) REQUIRE c.conversation_id IS UNIQUE;

CREATE CONSTRAINT message_id_unique IF NOT EXISTS
FOR (msg:Message) REQUIRE msg.message_id IS UNIQUE;
