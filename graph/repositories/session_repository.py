from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..models.session import Session
from .base_repository import BaseRepository


class SessionRepository(BaseRepository):
    label = "Session"
    id_field = "session_id"

    def start_session(self, session: Session) -> dict[str, Any]:
        node = self.merge(session.to_dict())
        query = """
        MATCH (s:Session {session_id: $session_id})
        MATCH (u:User {user_id: $user_id})
        MERGE (u)-[:HAS_SESSION]->(s)
        """
        self.client.execute_write(
            query, {"session_id": session.session_id, "user_id": session.user_id}
        )
        return node

    def end_session(self, session_id: str) -> dict[str, Any]:
        query = """
        MATCH (s:Session {session_id: $session_id})
        SET s.ended_at = $ended_at
        RETURN s
        """
        result = self.client.execute_write(
            query, {"session_id": session_id, "ended_at": datetime.now(timezone.utc).isoformat()}
        )
        return result[0]["s"] if result else {}
