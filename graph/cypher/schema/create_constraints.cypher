// ============================================================
// Uniqueness constraints — one per entity's id property.
// Run with: python -m graph.builders.graph_builder --schema
// ============================================================

CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.user_id IS UNIQUE;

CREATE CONSTRAINT track_id_unique IF NOT EXISTS
FOR (t:Track) REQUIRE t.track_id IS UNIQUE;

CREATE CONSTRAINT artist_id_unique IF NOT EXISTS
FOR (a:Artist) REQUIRE a.artist_id IS UNIQUE;

CREATE CONSTRAINT album_id_unique IF NOT EXISTS
FOR (al:Album) REQUIRE al.album_id IS UNIQUE;

CREATE CONSTRAINT playlist_id_unique IF NOT EXISTS
FOR (p:Playlist) REQUIRE p.playlist_id IS UNIQUE;

CREATE CONSTRAINT session_id_unique IF NOT EXISTS
FOR (s:Session) REQUIRE s.session_id IS UNIQUE;

CREATE CONSTRAINT memory_id_unique IF NOT EXISTS
FOR (m:Memory) REQUIRE m.memory_id IS UNIQUE;

CREATE CONSTRAINT preference_id_unique IF NOT EXISTS
FOR (p:Preference) REQUIRE p.preference_id IS UNIQUE;

CREATE CONSTRAINT conversation_id_unique IF NOT EXISTS
FOR (c:Conversation) REQUIRE c.conversation_id IS UNIQUE;

CREATE CONSTRAINT message_id_unique IF NOT EXISTS
FOR (msg:Message) REQUIRE msg.message_id IS UNIQUE;
