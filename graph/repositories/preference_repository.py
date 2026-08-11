from __future__ import annotations

from typing import Any

from ..models.preference import Preference
from .base_repository import BaseRepository


class PreferenceRepository(BaseRepository):
    label = "Preference"
    id_field = "preference_id"

    def upsert_preference(self, preference: Preference) -> dict[str, Any]:
        # ``preference_id`` is an assertion identifier, not the identity of a
        # listener's current preference. Merge by user/kind/value so a later
        # "not Song B" replaces the old signal instead of creating a tie.
        query = """
        MERGE (p:Preference {user_id: $user_id, kind: $kind, value_key: toLower($value)})
        ON CREATE SET p.preference_id = $preference_id, p.created_at = $updated_at
        SET p.value = $value, p.strength = $strength, p.sentiment = $sentiment,
            p.updated_at = $updated_at
        WITH p
        MATCH (u:User {user_id: $user_id})
        MERGE (u)-[:HAS_PREFERENCE]->(p)
        RETURN p
        """
        result = self.client.execute_write(query, preference.to_dict())
        node = result[0]["p"] if result else preference.to_dict()
        return node

    def get_for_user(self, user_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_PREFERENCE]->(p:Preference)
        RETURN p
        ORDER BY p.strength DESC
        """
        result = self.client.execute_read(query, {"user_id": user_id})
        return [r["p"] for r in result]
