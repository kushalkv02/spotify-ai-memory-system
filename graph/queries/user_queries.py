GET_USER_WITH_PREFERENCES = """
MATCH (u:User {user_id: $user_id})
OPTIONAL MATCH (u)-[:HAS_PREFERENCE]->(p:Preference)
RETURN u, collect(p) AS preferences
"""

GET_USER_PLAY_COUNT = """
MATCH (u:User {user_id: $user_id})-[r:PLAYED]->(:Track)
RETURN count(r) AS play_count
"""
