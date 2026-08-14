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

// Recommend unplayed tracks in genres the user has listened to or explicitly
// marked as liked. This lets a saved statement such as "I like electronic"
// work before the user has recorded an electronic play.
// params: $user_id, $limit
CALL {
    MATCH (me:User {user_id: $user_id})-[:PLAYED]->(seed:Track)
    WHERE seed.genre IS NOT NULL AND trim(seed.genre) <> ''
    RETURN trim(seed.genre) AS genre, count(DISTINCT seed) AS play_affinity,
           0.0 AS preference_affinity

    UNION ALL

    MATCH (me:User {user_id: $user_id})-[:HAS_PREFERENCE]->(preference:Preference)
    WHERE preference.kind = 'genre'
      AND preference.sentiment = 'like'
      AND preference.value IS NOT NULL
      AND trim(preference.value) <> ''
    RETURN trim(preference.value) AS genre, 0 AS play_affinity,
           coalesce(preference.strength, 1.0) AS preference_affinity
}
WITH toLower(genre) AS genre_key,
     sum(play_affinity) + sum(preference_affinity) AS genre_affinity
MATCH (rec:Track)
WHERE rec.genre IS NOT NULL
  AND toLower(trim(rec.genre)) = genre_key
  AND NOT EXISTS {
      MATCH (:User {user_id: $user_id})-[:PLAYED]->(rec)
  }
RETURN rec.track_id AS track_id, rec.title AS title, rec.genre AS genre,
       genre_affinity
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
