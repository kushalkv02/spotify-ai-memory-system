TOP_TRACKS_QUERY = """
MATCH (:User {user_id: $user_id})-[r:PLAYED]->(t:Track)
RETURN t.track_id AS track_id, t.title AS title, count(r) AS play_count
ORDER BY play_count DESC
LIMIT $limit
"""

TOP_ARTISTS_QUERY = """
MATCH (:User {user_id: $user_id})-[:PLAYED]->(:Track)<-[:BY]-(ar:Artist)
RETURN ar.artist_id AS artist_id, ar.name AS name, count(*) AS play_count
ORDER BY play_count DESC
LIMIT $limit
"""
