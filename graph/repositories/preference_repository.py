from __future__ import annotations

from typing import Any

from ..models.preference import Preference
from .base_repository import BaseRepository


class PreferenceRepository(BaseRepository):
    label = "Preference"
    id_field = "preference_id"

    def upsert_preference(self, preference: Preference) -> dict[str, Any]:
        node = self.merge(preference.to_dict())
        query = """
        MATCH (p:Preference {preference_id: $preference_id})
        MATCH (u:User {user_id: $user_id})
        MERGE (u)-[:HAS_PREFERENCE]->(p)
        """
        self.client.execute_write(
            query, {"preference_id": preference.preference_id, "user_id": preference.user_id}
        )
        return node

    def get_for_user(self, user_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_PREFERENCE]->(p:Preference)
        RETURN p
        ORDER BY p.strength DESC
        """
        result = self.client.execute_read(query, {"user_id": user_id})
        return [r["p"] for r in result]
