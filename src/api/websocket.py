"""WebSocket connection manager for live simulation event streaming.

Manages active WebSocket connections, per-connection event type filters,
and broadcasts BusEvents from the EventBus to all connected clients.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import WebSocket

from src.api.converters import bus_event_to_schema

if TYPE_CHECKING:
    from src.types import BusEvent

logger = logging.getLogger("agent_civilisation.api.websocket")


class ConnectionManager:
    """Manages WebSocket connections and broadcasts simulation events.

    Each connection tracks an optional filter set. When the filter is None
    the client receives all events. Clients can send a JSON message:

        {"subscribe": ["AGENT_MOVED", "MESSAGE_SENT"]}

    to restrict which BusEventType values they receive. An empty list
    resets to receiving everything.
    """

    def __init__(self) -> None:
        # Each entry is (websocket, filter_set_or_None).
        self.active_connections: list[tuple[WebSocket, set[str] | None]] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection (no filter — receives all events)."""
        await websocket.accept()
        self.active_connections.append((websocket, None))
        logger.info("WebSocket client connected (%d total)", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket."""
        self.active_connections = [
            (ws, f) for ws, f in self.active_connections if ws is not websocket
        ]
        logger.info("WebSocket client disconnected (%d remaining)", len(self.active_connections))

    async def handle_subscription(self, websocket: WebSocket, data: dict) -> None:
        """Process a subscription filter message from a client.

        Expected format:
            {"subscribe": ["AGENT_MOVED", "TICK_START", ...]}

        An empty list resets the filter to receive all events.
        """
        event_types = data.get("subscribe", [])
        if not isinstance(event_types, list):
            return

        new_filter: set[str] | None = set(event_types) if event_types else None

        self.active_connections = [
            (ws, new_filter if ws is websocket else f)
            for ws, f in self.active_connections
        ]
        logger.debug(
            "WebSocket subscription updated: %s",
            new_filter if new_filter else "all events",
        )

    async def broadcast(self, event: BusEvent) -> None:
        """Send a BusEvent to all connected clients (respecting filters).

        This method is registered as an async subscriber on the EventBus
        via `event_bus.subscribe_async(manager.broadcast)`.

        Disconnected clients are silently removed.
        """
        if not self.active_connections:
            return

        schema = bus_event_to_schema(event)
        payload = schema.model_dump(mode="json")
        event_type_str = payload.get("type", "")

        stale: list[WebSocket] = []

        for ws, filter_set in self.active_connections:
            # Skip if client has a filter that does not include this event type.
            if filter_set is not None and event_type_str not in filter_set:
                continue

            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)

        # Remove disconnected clients.
        if stale:
            stale_set = set(id(ws) for ws in stale)
            self.active_connections = [
                (ws, f) for ws, f in self.active_connections if id(ws) not in stale_set
            ]
            logger.info("Removed %d stale WebSocket connections", len(stale))


# Module-level singleton — used by routes.py and server.py.
manager = ConnectionManager()
