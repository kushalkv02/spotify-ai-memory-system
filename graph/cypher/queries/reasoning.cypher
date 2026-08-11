// ============================================================
// Reference queries used to EXPLAIN a recommendation (for the
// explanation_service) by walking the memory/preference graph.
// Mirrored as parametrized strings in graph/queries/temporal_queries.py
// and graph/queries/analytics_queries.py
// ============================================================

// Why was `rec_track_id` recommended to `user_id`? Show the connecting path.
// params: $user_id, $rec_track_id
MATCH path = (u:User {user_id: $user_id})-[:PLAYED]->(t:Track)<-[:BY]-(ar:Artist)-[:BY]->(rec:Track {track_id: $rec_track_id})
RETURN [n IN nodes(path) | coalesce(n.title, n.name, n.user_id)] AS explanation_path
LIMIT 5;

// Memories that most plausibly justify a recommendation, ranked by importance.
// params: $user_id
MATCH (m:Memory)-[:ABOUT]->(u:User {user_id: $user_id})
RETURN m.summary AS summary, m.importance AS importance
ORDER BY m.importance DESC
LIMIT 10;
