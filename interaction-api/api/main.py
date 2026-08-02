"""
FastAPI application entrypoint for the Interaction API.

Vue.js Client
     │
     ▼ (Playback Events / Chat / UI Actions)
Interaction API (FastAPI)   <-- this file
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import settings
from ..db.postgres_client import postgres_client
from ..integrations.graph_client import graph_client
from ..services.client_state_service import client_state
from .routes import auth_routes, catalog_routes, chat_routes, interaction_routes, health_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await postgres_client.connect()
    await graph_client.seed_artists(client_state.featured_artists(), client_state.tracks)
    yield
    await postgres_client.disconnect()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_origin_regex=settings.cors_allowed_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_routes.router)
    app.include_router(auth_routes.router)
    app.include_router(interaction_routes.router)
    app.include_router(catalog_routes.router)
    app.include_router(chat_routes.router)
    return app


app = create_app()
