from __future__ import annotations

from typing import Any, Optional

from ..models.user import User
from .base_repository import BaseRepository


class UserRepository(BaseRepository):
    label = "User"
    id_field = "user_id"

    def create_user(self, user: User) -> dict[str, Any]:
        return self.merge(user.to_dict())

    def get_user(self, user_id: str) -> Optional[dict[str, Any]]:
        return self.get_by_id(user_id)

    def set_consent(self, user_id: str, consent_given: bool) -> dict[str, Any]:
        query = """
        MATCH (u:User {user_id: $user_id})
        SET u.consent_given = $consent_given
        RETURN u
        """
        result = self.client.execute_write(
            query, {"user_id": user_id, "consent_given": consent_given}
        )
        return result[0]["u"] if result else {}
