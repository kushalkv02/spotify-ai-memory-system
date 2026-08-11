GENRE_AFFINITY_REASONING_QUERY = """
MATCH (u:User {user_id: $user_id})-[:PLAYED]->(t:Track)
WHERE t.genre IS NOT NULL
RETURN t.genre AS genre, count(*) AS play_count
ORDER BY play_count DESC
"""

MOOD_AFFINITY_REASONING_QUERY = """
MATCH (u:User {user_id: $user_id})-[:PLAYED]->(t:Track)
WHERE t.mood IS NOT NULL
RETURN t.mood AS mood, count(*) AS play_count
ORDER BY play_count DESC
"""