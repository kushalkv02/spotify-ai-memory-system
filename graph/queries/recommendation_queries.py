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
MATCH (me:User {user_id: $user_id})-[:PLAYED]->(:Track)<-[:PERFORMED]-(ar:Artist)
MATCH (ar)-[:PERFORMED]->(rec:Track)
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
