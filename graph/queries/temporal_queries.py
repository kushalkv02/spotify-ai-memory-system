RECENT_PLAY_TIMELINE_QUERY = """
MATCH (u:User {user_id: $user_id})-[r:PLAYED]->(t:Track)
WHERE datetime(r.played_at) >= datetime() - duration({days: $days})
RETURN t.track_id AS track_id, t.title AS title, r.played_at AS played_at
ORDER BY r.played_at DESC
"""
