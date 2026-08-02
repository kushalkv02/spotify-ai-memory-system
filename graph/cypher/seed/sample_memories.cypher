// ============================================================
// Sample Memory nodes. Run AFTER user_seed.cypher and music_seed.cypher
// since it MATCHes existing User/Track nodes.
// (Memory)-[:ABOUT]->(User), (Memory)-[:REFERENCES]->(Track)
// ============================================================

MERGE (m1:Memory {memory_id: 'memory_001'})
SET m1.summary = 'User replayed "The Less I Know the Better" three times in one evening session, skipping most other tracks.',
    m1.importance = 0.8,
    m1.created_at = datetime();

WITH 1 AS _
MATCH (u:User {user_id: 'user_001'}), (m1:Memory {memory_id: 'memory_001'})
MERGE (m1)-[:ABOUT]->(u);

WITH 1 AS _
MATCH (m1:Memory {memory_id: 'memory_001'}), (t:Track {track_id: 'track_001'})
MERGE (m1)-[:REFERENCES]->(t);
