"""FastAPI application for the Agent Civilisation REST API and WebSocket feed.

This module creates the FastAPI app, configures CORS middleware, and provides
a SimulationState container that holds references to the live simulation
objects. The `create_app()` factory is the main entry point.

Usage from scripts/run.py:

    from src.api.server import create_app, sim_state
    sim_state.world_state = engine.state
    sim_state.event_bus = event_bus
    sim_state.chronicle = chronicle
    sim_state.config = config
    app = create_app()
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.types import EventBus, WorldState
    from src.watcher.chronicle import Chronicle


class SimulationState:
    """Holds references to the running simulation for API access.

    Populated at startup by the run script before the server begins
    accepting requests. All API route handlers read from this singleton.
    """

    def __init__(self) -> None:
        self.world_state: WorldState | None = None
        self.event_bus: EventBus | None = None
        self.chronicle: Chronicle | None = None
        self.config: SimulationConfig | None = None
        self.start_time: float = time.time()


# Module-level singleton — populated by the run script.
sim_state = SimulationState()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns a fully wired app with CORS middleware, REST routes,
    and the WebSocket endpoint. The caller must populate `sim_state`
    before starting uvicorn.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup: register the WebSocket manager as an async subscriber
        # on the event bus so it receives every BusEvent.
        from src.api.websocket import manager

        if sim_state.event_bus is not None:
            sim_state.event_bus.subscribe_async(manager.broadcast)

        yield

        # Shutdown: disconnect all WebSocket clients.
        for ws, _ in list(manager.active_connections):
            try:
                await ws.close()
            except Exception:
                pass
        manager.active_connections.clear()

    app = FastAPI(
        title="Agent Civilisation API",
        description="REST API and WebSocket feed for the Agent Civilisation simulation.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS: allow all origins in development, restrict in production via env var.
    allowed_origins_env = os.environ.get("CORS_ALLOWED_ORIGINS", "")
    if allowed_origins_env:
        allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    else:
        allowed_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include REST + WebSocket routes.
    from src.api.routes import router

    app.include_router(router)

    return app
