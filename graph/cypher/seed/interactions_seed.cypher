// ============================================================
// Sample interaction edges: PLAYED, LIKED, SKIPPED, FOLLOWED.
// Run AFTER user_seed.cypher and music_seed.cypher (this file
// MATCHes those nodes, it doesn't create new ones).
//
// PLAYED and SKIPPED are events, so this uses CREATE for those
// (repeated calls will add more history, which is intentional).
// LIKED and FOLLOWED are state, so this uses MERGE (repeated
// calls are idempotent).
//
// Designed so collaborative filtering / artist-affinity queries in
// graph/cypher/queries/recommendations.cypher produce real results:
// user_001 and user_002 share several plays, user_003 leans hip hop,
// user_004 barely listens yet (good for testing "cold start").
// ============================================================

// -- user_001 (Kushal): heavy Tame Impala / Daft Punk listener -----------------------------------------------------
WITH 1 AS _
MATCH (u:User {user_id: 'user_001'}), (t:Track {track_id: 'track_001'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('P2D'), ms_played: 216320, context: 'seed', session_id: 'session_seed_001'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_001'}), (t:Track {track_id: 'track_001'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('P1D'), ms_played: 216320, context: 'seed', session_id: 'session_seed_002'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_001'}), (t:Track {track_id: 'track_002'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('P1D'), ms_played: 467000, context: 'seed', session_id: 'session_seed_002'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_001'}), (t:Track {track_id: 'track_003'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('PT12H'), ms_played: 369000, context: 'seed', session_id: 'session_seed_003'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_001'}), (t:Track {track_id: 'track_009'})
CREATE (u)-[:SKIPPED {skipped_at: datetime() - duration('PT11H'), ms_played: 8000, context: 'seed', session_id: 'session_seed_003'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_001'}), (t:Track {track_id: 'track_001'})
MERGE (u)-[r:LIKED]->(t)
SET r.liked_at = datetime() - duration('P1D');

WITH 1 AS _
MATCH (u:User {user_id: 'user_001'}), (ar:Artist {artist_id: 'artist_001'})
MERGE (u)-[r:FOLLOWED]->(ar)
SET r.followed_at = datetime() - duration('P30D');

// -- user_002 (Test User): overlaps with user_001 on Tame Impala, also likes Daft Punk -----------------------------------------------------
WITH 1 AS _
MATCH (u:User {user_id: 'user_002'}), (t:Track {track_id: 'track_001'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('P3D'), ms_played: 216320, context: 'seed', session_id: 'session_seed_004'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_002'}), (t:Track {track_id: 'track_003'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('P2D'), ms_played: 369000, context: 'seed', session_id: 'session_seed_005'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_002'}), (t:Track {track_id: 'track_004'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('P2D'), ms_played: 320000, context: 'seed', session_id: 'session_seed_005'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_002'}), (t:Track {track_id: 'track_005'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('P2D'), ms_played: 100000, context: 'seed', session_id: 'session_seed_005'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_002'}), (t:Track {track_id: 'track_005'})
CREATE (u)-[:SKIPPED {skipped_at: datetime() - duration('P2D'), ms_played: 100000, context: 'seed', session_id: 'session_seed_005'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_002'}), (t:Track {track_id: 'track_003'})
MERGE (u)-[rel:LIKED]->(t)
SET rel.liked_at = datetime() - duration('P2D');

WITH 1 AS _
MATCH (u:User {user_id: 'user_002'}), (ar:Artist {artist_id: 'artist_002'})
MERGE (u)-[r:FOLLOWED]->(ar)
SET r.followed_at = datetime() - duration('P20D');

// -- user_003 (Priya): hip hop / Kendrick Lamar listener -----------------------------------------------------
WITH 1 AS _
MATCH (u:User {user_id: 'user_003'}), (t:Track {track_id: 'track_010'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('P1D'), ms_played: 177000, context: 'seed', session_id: 'session_seed_006'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_003'}), (t:Track {track_id: 'track_011'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('P1D'), ms_played: 185000, context: 'seed', session_id: 'session_seed_006'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_003'}), (t:Track {track_id: 'track_012'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('PT6H'), ms_played: 234000, context: 'seed', session_id: 'session_seed_007'}]->(t);

WITH 1 AS _
MATCH (u:User {user_id: 'user_003'}), (t:Track {track_id: 'track_010'})
MERGE (u)-[rel:LIKED]->(t)
SET rel.liked_at = datetime() - duration('P1D');

WITH 1 AS _
MATCH (u:User {user_id: 'user_003'}), (ar:Artist {artist_id: 'artist_004'})
MERGE (u)-[r:FOLLOWED]->(ar)
SET r.followed_at = datetime() - duration('P10D');

WITH 1 AS _
MATCH (u:User {user_id: 'user_003'}), (t:Track {track_id: 'track_008'})
CREATE (u)-[:SKIPPED {skipped_at: datetime() - duration('PT5H'), ms_played: 4000, context: 'seed', session_id: 'session_seed_007'}]->(t);

// -- user_004 (Sam): cold start, one play only -----------------------------------------------------
WITH 1 AS _
MATCH (u:User {user_id: 'user_004'}), (t:Track {track_id: 'track_009'})
CREATE (u)-[:PLAYED {played_at: datetime() - duration('PT2H'), ms_played: 174000, context: 'seed', session_id: 'session_seed_008'}]->(t);
