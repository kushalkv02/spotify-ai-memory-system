// ============================================================
// Reference queries for track recommendations.
// Mirrored as parametrized strings in graph/queries/recommendation_queries.py
// ============================================================

// Naive collaborative filtering:
// "users who played what I played also played these tracks"
// params: $user_id, $limit
MATCH (me:User {user_id: $user_id})-[:PLAYED]->(t:Track)<-[:PLAYED]-(other:User)
MATCH (other)-[:PLAYED]->(rec:Track)
WHERE NOT (me)-[:PLAYED]->(rec)
RETURN rec.track_id AS track_id, rec.title AS title, count(DISTINCT other) AS shared_listeners
ORDER BY shared_listeners DESC
LIMIT $limit;

// Recommend unplayed tracks in genres the user has already listened to.
// params: $user_id, $limit
MATCH (me:User {user_id: $user_id})-[:PLAYED]->(seed:Track)
MATCH (rec:Track)
WHERE rec.genre = seed.genre
  AND NOT (me)-[:PLAYED]->(rec)
RETURN rec.track_id AS track_id, rec.title AS title, rec.genre AS genre,
       count(DISTINCT seed) AS genre_affinity
ORDER BY genre_affinity DESC, rec.title ASC
LIMIT $limit;

// Recommend tracks by artists the user already plays a lot, but hasn't
// played this particular track yet.
// params: $user_id, $limit
MATCH (me:User {user_id: $user_id})-[:PLAYED]->(:Track)<-[:BY]-(ar:Artist)
MATCH (ar)-[:BY]->(rec:Track)
WHERE NOT (me)-[:PLAYED]->(rec)
RETURN rec.track_id AS track_id, rec.title AS title, ar.name AS artist, count(*) AS affinity
ORDER BY affinity DESC
LIMIT $limit;
