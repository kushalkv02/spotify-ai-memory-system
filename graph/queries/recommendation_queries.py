COLLABORATIVE_FILTER_QUERY = """
MATCH (me:User {user_id: $user_id})-[:PLAYED]->(t:Track)<-[:PLAYED]-(other:User)
MATCH (other)-[:PLAYED]->(rec:Track)
WHERE NOT (me)-[:PLAYED]->(rec)
RETURN rec.track_id AS track_id, rec.title AS title,
       count(DISTINCT other) AS shared_listeners
ORDER BY shared_listeners DESC
LIMIT $limit
"""

ARTIST_AFFINITY_QUERY = """
MATCH (me:User {user_id: $user_id})-[:PLAYED]->(:Track)-[:BY]->(ar:Artist)
MATCH (rec:Track)-[:BY]->(ar:Artist)
WHERE NOT (me)-[:PLAYED]->(rec)
RETURN rec.track_id AS track_id, rec.title AS title, ar.name AS artist,
       count(*) AS affinity
ORDER BY affinity DESC
LIMIT $limit
"""

GENRE_AFFINITY_QUERY = """
MATCH (me:User {user_id: $user_id})-[:PLAYED]->(seed:Track)
MATCH (rec:Track)
WHERE rec.genre = seed.genre
  AND NOT (me)-[:PLAYED]->(rec)
RETURN rec.track_id AS track_id, rec.title AS title, rec.genre AS genre,
       count(DISTINCT seed) AS genre_affinity
ORDER BY genre_affinity DESC, rec.title ASC
LIMIT $limit
"""

MOOD_AFFINITY_QUERY = """
MATCH (me:User {user_id: $user_id})-[:PLAYED]->(seed:Track)
MATCH (rec:Track)
WHERE rec.mood = seed.mood
  AND NOT (me)-[:PLAYED]->(rec)
RETURN rec.track_id AS track_id, rec.title AS title, rec.mood AS mood,
       count(DISTINCT seed) AS mood_affinity
ORDER BY mood_affinity DESC, rec.title ASC
LIMIT $limit
"""

RECENT_PLAY_TIMELINE_QUERY = """
MATCH (u:User {user_id: $user_id})-[:PLAYED]->(t:Track)
WHERE datetime(t.played_at) >= datetime() - duration({days: $days})
RETURN t.track_id AS track_id, t.title AS title, t.played_at AS played_at
ORDER BY t.played_at DESC
"""