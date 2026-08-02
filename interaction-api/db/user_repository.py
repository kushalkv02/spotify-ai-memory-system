"""Postgres-backed account repository."""
from __future__ import annotations

from typing import Any

from .postgres_client import PostgresClient


class UserRepository:
    def __init__(self, pg_client: PostgresClient):
        self.pg_client = pg_client

    async def get_by_login(self, login: str) -> dict[str, Any] | None:
        async with self.pg_client.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE login = $1", login)
        return dict(row) if row else None

    async def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        async with self.pg_client.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return dict(row) if row else None

    async def create(self, *, user_id: str, login: str, email: str, display_name: str, password_hash: str) -> dict[str, Any]:
        query = """
            INSERT INTO users (id, login, email, display_name, password_hash)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """
        async with self.pg_client.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, login, email, display_name, password_hash)
        return dict(row)

    async def mark_logged_in(self, user_id: str) -> dict[str, Any] | None:
        async with self.pg_client.pool.acquire() as conn:
            row = await conn.fetchrow(
                "UPDATE users SET last_login_at = now() WHERE id = $1 RETURNING *", user_id
            )
        return dict(row) if row else None

    async def delete(self, user_id: str) -> None:
        async with self.pg_client.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)
