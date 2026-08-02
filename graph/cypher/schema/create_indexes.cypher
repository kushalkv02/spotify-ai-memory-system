// ============================================================
// Secondary indexes for common lookups / sorts.
// Run with: python -m graph.builders.graph_builder --schema
// ============================================================

CREATE INDEX track_title_idx IF NOT EXISTS
FOR (t:Track) ON (t.title);

CREATE INDEX artist_name_idx IF NOT EXISTS
FOR (a:Artist) ON (a.name);

CREATE INDEX user_email_idx IF NOT EXISTS
FOR (u:User) ON (u.email);

CREATE INDEX memory_created_at_idx IF NOT EXISTS
FOR (m:Memory) ON (m.created_at);

CREATE INDEX session_started_at_idx IF NOT EXISTS
FOR (s:Session) ON (s.started_at);

// Relationship-property index — speeds up "recent plays" style queries.
CREATE INDEX played_at_idx IF NOT EXISTS
FOR ()-[r:PLAYED]-() ON (r.played_at);

CREATE INDEX liked_at_idx IF NOT EXISTS
FOR ()-[r:LIKED]-() ON (r.liked_at);

CREATE INDEX skipped_at_idx IF NOT EXISTS
FOR ()-[r:SKIPPED]-() ON (r.skipped_at);

CREATE INDEX followed_at_idx IF NOT EXISTS
FOR ()-[r:FOLLOWED]-() ON (r.followed_at);
