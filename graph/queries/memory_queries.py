RECENT_MEMORIES_FOR_USER = """
MATCH (m:Memory)-[:ABOUT]->(u:User {user_id: $user_id})
RETURN m.memory_id AS memory_id, m.summary AS summary,
       m.importance AS importance, m.created_at AS created_at
ORDER BY m.created_at DESC
LIMIT $limit
"""

MEMORIES_REFERENCING_TRACK = """
MATCH (m:Memory)-[:REFERENCES]->(t:Track {track_id: $track_id})
RETURN m.memory_id AS memory_id, m.summary AS summary,
       m.importance AS importance, m.created_at AS created_at
ORDER BY m.created_at DESC
"""
