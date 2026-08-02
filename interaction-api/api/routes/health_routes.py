"""Liveness/readiness endpoints."""
from fastapi import APIRouter, Depends

from ..dependencies import get_postgres_client
from ...db.postgres_client import PostgresClient
from ...integrations.graph_client import graph_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness():
    return {"status": "ok"}


@router.get("/ready")
async def readiness(pg: PostgresClient = Depends(get_postgres_client)):
    pg_ok = await pg.ping()
    return {
        "postgres": "ok" if pg_ok else "unreachable",
        "graph_writeback_enabled": graph_client.enabled,
    }
