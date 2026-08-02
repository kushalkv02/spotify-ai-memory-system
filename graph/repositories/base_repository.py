"""
Generic repository providing MERGE / GET / DELETE / LIST for a single
node label. Concrete repositories subclass this and set `label` +
`id_field`; most only need a couple of entity-specific extra methods
on top (see user_repository.py / track_repository.py for examples).
"""
from __future__ import annotations

from typing import Any, Optional

from ..neo4j_client import get_client


class BaseRepository:
    label: str = "Node"
    id_field: str = "id"

    def __init__(self) -> None:
        self.client = get_client()

    def merge(self, properties: dict[str, Any]) -> dict[str, Any]:
        """
        Create-or-update a node by its id field. Idempotent — safe to
        call every time an entity is seen (e.g. every incoming event).
        """
        if self.id_field not in properties:
            raise ValueError(f"'{self.id_field}' is required to merge a {self.label}")

        other_props = {k: v for k, v in properties.items() if k != self.id_field}
        set_clause = ", ".join(f"n.{k} = ${k}" for k in other_props) or "n.updated_at = n.updated_at"

        query = f"""
        MERGE (n:{self.label} {{{self.id_field}: $id_value}})
        SET {set_clause}
        RETURN n
        """
        params = {**other_props, "id_value": properties[self.id_field]}
        result = self.client.execute_write(query, params)
        return result[0]["n"] if result else {}

    def get_by_id(self, id_value: str) -> Optional[dict[str, Any]]:
        query = f"MATCH (n:{self.label} {{{self.id_field}: $id_value}}) RETURN n"
        result = self.client.execute_read(query, {"id_value": id_value})
        return result[0]["n"] if result else None

    def exists(self, id_value: str) -> bool:
        return self.get_by_id(id_value) is not None

    def delete(self, id_value: str) -> None:
        query = f"MATCH (n:{self.label} {{{self.id_field}: $id_value}}) DETACH DELETE n"
        self.client.execute_write(query, {"id_value": id_value})

    def list_all(self, limit: int = 100) -> list[dict[str, Any]]:
        query = f"MATCH (n:{self.label}) RETURN n LIMIT $limit"
        result = self.client.execute_read(query, {"limit": limit})
        return [r["n"] for r in result]

    def count(self) -> int:
        query = f"MATCH (n:{self.label}) RETURN count(n) AS c"
        result = self.client.execute_read(query)
        return result[0]["c"] if result else 0
