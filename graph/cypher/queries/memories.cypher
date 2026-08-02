// ============================================================
// Reference queries for Memory nodes.
// Mirrored as parametrized strings in graph/queries/memory_queries.py
// ============================================================

// Most recent memories for a user
// params: $user_id, $limit
MATCH (m:Memory)-[:ABOUT]->(u:User {user_id: $user_id})
RETURN m.memory_id AS memory_id, m.summary AS summary, m.importance AS importance, m.created_at AS created_at
ORDER BY m.created_at DESC
LIMIT $limit;

// Memories that reference a given track
// params: $track_id
MATCH (m:Memory)-[:REFERENCES]->(t:Track {track_id: $track_id})
RETURN m.memory_id AS memory_id, m.summary AS summary,
       m.importance AS importance, m.created_at AS created_at
ORDER BY m.created_at DESC;
