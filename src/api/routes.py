"""REST and WebSocket route handlers for the Agent Civilisation API.

All endpoints read from the module-level SimulationState singleton
(src.api.server.sim_state). If the simulation has not yet been
initialised, endpoints return HTTP 503.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from src.api.converters import (
    agent_to_detail,
    agents_to_list_response,
    chronicle_to_response,
    config_to_response,
    innovations_to_list_response,
    interactions_to_response,
    memories_to_response,
    milestones_to_response,
    narratives_to_response,
    recipes_to_list_response,
    rules_to_list_response,
    specialisations_to_response,
    structures_to_list_response,
    world_state_to_response,
    world_state_to_stats,
)
from src.api.schemas import (
    AgentDetailResponse,
    AgentListResponse,
    ChronicleEntrySchema,
    ChronicleResponse,
    ConfigResponse,
    InnovationListResponse,
    InteractionListResponse,
    MemoryListResponse,
    MilestoneListResponse,
    NarrativeListResponse,
    RecipeListResponse,
    RuleListResponse,
    SpecialisationResponse,
    StatsResponse,
    StructureListResponse,
    WorldStateResponse,
)
from src.api.server import sim_state
from src.api.websocket import manager

logger = logging.getLogger("agent_civilisation.api.routes")

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_simulation():
    """Raise 503 if the simulation is not yet initialised."""
    if sim_state.world_state is None:
        raise HTTPException(
            status_code=503,
            detail="Simulation not yet initialised. Please wait for startup to complete.",
        )


def _get_agent(agent_id: int):
    """Look up an agent by ID, raising 404 if not found."""
    _require_simulation()
    agent = sim_state.world_state.agents.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found.")
    return agent


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@router.get("/api/health")
async def health():
    """Health check endpoint for monitoring and load balancers."""
    ws = sim_state.world_state
    if ws is None:
        return {
            "status": "initializing",
            "tick": 0,
            "agents": 0,
            "uptime": time.time() - sim_state.start_time,
        }
    return {
        "status": "running",
        "tick": ws.tick,
        "agents": len(ws.agents),
        "uptime": time.time() - sim_state.start_time,
    }


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------

@router.get("/api/state", response_model=WorldStateResponse)
async def get_state():
    """Current world state snapshot."""
    _require_simulation()
    return world_state_to_response(sim_state.world_state)


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

@router.get("/api/agents", response_model=AgentListResponse)
async def get_agents():
    """All agent summaries."""
    _require_simulation()
    return agents_to_list_response(sim_state.world_state.agents)


@router.get("/api/agents/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(agent_id: int):
    """Full detail for a single agent."""
    agent = _get_agent(agent_id)
    return agent_to_detail(agent)


@router.get("/api/agents/{agent_id}/memories", response_model=MemoryListResponse)
async def get_agent_memories(agent_id: int):
    """All memories for a single agent."""
    agent = _get_agent(agent_id)
    return memories_to_response(agent)


@router.get("/api/agents/{agent_id}/interactions", response_model=InteractionListResponse)
async def get_agent_interactions(
    agent_id: int,
    partner_id: Optional[int] = Query(default=None, description="Filter to interactions with a specific partner"),
):
    """Messages involving a specific agent.

    Optionally filter by partner_id to see only interactions between
    the agent and that specific partner.
    """
    _get_agent(agent_id)  # validate existence
    messages = sim_state.world_state.message_log

    if partner_id is not None:
        # Filter to messages between agent_id and partner_id.
        messages = [
            m for m in messages
            if (m.sender_id == agent_id and m.receiver_id == partner_id)
            or (m.sender_id == partner_id and m.receiver_id == agent_id)
        ]
        return InteractionListResponse(
            agent_id=agent_id,
            messages=[
                _msg_to_schema(m) for m in messages
            ],
        )

    return interactions_to_response(agent_id, messages)


def _msg_to_schema(msg):
    """Inline helper — avoids importing MessageSchema converter at module level."""
    from src.api.converters import message_to_schema
    return message_to_schema(msg)


# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------

@router.get("/api/structures", response_model=StructureListResponse)
async def get_structures():
    """All structures in the world with their positions."""
    _require_simulation()
    return structures_to_list_response(sim_state.world_state)


@router.get("/api/structures/innovations", response_model=InnovationListResponse)
async def get_innovations():
    """Only structures with a custom_name (agent innovations)."""
    _require_simulation()
    return innovations_to_list_response(sim_state.world_state)


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

@router.get("/api/recipes", response_model=RecipeListResponse)
async def get_recipes():
    """All discovered composition recipes."""
    _require_simulation()
    return recipes_to_list_response(sim_state.world_state.discovered_recipes)


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

@router.get("/api/rules", response_model=RuleListResponse)
async def get_rules():
    """All collective rules with summary counts."""
    _require_simulation()
    return rules_to_list_response(sim_state.world_state.collective_rules)


# ---------------------------------------------------------------------------
# Specialisations
# ---------------------------------------------------------------------------

@router.get("/api/specialisations", response_model=SpecialisationResponse)
async def get_specialisations():
    """Aggregated specialisation data across all agents."""
    _require_simulation()
    return specialisations_to_response(sim_state.world_state.agents)


# ---------------------------------------------------------------------------
# Chronicle
# ---------------------------------------------------------------------------

@router.get("/api/chronicle", response_model=ChronicleResponse)
async def get_chronicle(
    since_tick: int = Query(default=0, ge=0, description="Only entries from this tick onward"),
    until_tick: Optional[int] = Query(default=None, ge=0, description="Only entries up to this tick"),
    type: Optional[str] = Query(default=None, alias="type", description="Filter by entry type"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: Optional[int] = Query(default=None, ge=1, description="Max entries to return"),
):
    """Paginated chronicle entries with optional filters."""
    _require_simulation()
    if sim_state.chronicle is None:
        return ChronicleResponse(entries=[], total=0)

    reports = sim_state.chronicle.get_reports(
        since_tick=since_tick,
        until_tick=until_tick,
        type_filter=type,
    )

    total = len(reports)
    sliced = reports[offset:] if limit is None else reports[offset:offset + limit]

    entries = [
        ChronicleEntrySchema(
            type=r["type"],
            tick=r["tick"],
            timestamp=r["timestamp"],
            data=r["data"],
        )
        for r in sliced
    ]

    return ChronicleResponse(entries=entries, total=total)


@router.get("/api/chronicle/milestones", response_model=MilestoneListResponse)
async def get_milestones():
    """All milestones reached so far."""
    _require_simulation()

    # Prefer chronicle milestones (watcher-produced).
    if sim_state.chronicle is not None:
        raw = sim_state.chronicle.get_milestones()
        from src.api.schemas import MilestoneSchema
        milestones = [
            MilestoneSchema(
                name=m["data"].get("name", "Unknown"),
                tick=m["tick"],
                commentary=m["data"].get("commentary", ""),
            )
            for m in raw
        ]
        return MilestoneListResponse(milestones=milestones)

    # Fallback: extract from event bus log.
    if sim_state.event_bus is not None:
        events = sim_state.event_bus.get_log()
        return milestones_to_response(events)

    return MilestoneListResponse(milestones=[])


@router.get("/api/chronicle/narratives", response_model=NarrativeListResponse)
async def get_narratives():
    """All narrative passages generated so far."""
    _require_simulation()

    # Prefer chronicle narratives.
    if sim_state.chronicle is not None:
        reports = sim_state.chronicle.get_reports(type_filter="narrative")
        from src.api.schemas import NarrativeSchema
        narratives = [
            NarrativeSchema(
                tick=r["tick"],
                text=r["data"].get("text", ""),
            )
            for r in reports
        ]
        return NarrativeListResponse(narratives=narratives)

    # Fallback: extract from event bus log.
    if sim_state.event_bus is not None:
        events = sim_state.event_bus.get_log()
        return narratives_to_response(events)

    return NarrativeListResponse(narratives=[])


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Aggregate simulation statistics."""
    _require_simulation()
    return world_state_to_stats(sim_state.world_state)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@router.get("/api/config", response_model=ConfigResponse)
async def get_config():
    """Full simulation configuration (read-only)."""
    _require_simulation()
    if sim_state.config is None:
        raise HTTPException(status_code=503, detail="Configuration not available.")
    return config_to_response(sim_state.config)


# ---------------------------------------------------------------------------
# Historical state
# ---------------------------------------------------------------------------

@router.get("/api/state/history/{tick}", response_model=WorldStateResponse)
async def get_state_history(tick: int):
    """World state from a persistence snapshot.

    The simulation saves state to disk every `save_interval` ticks.
    This endpoint loads the most recent snapshot at or before the
    requested tick. Returns 404 if no snapshot is available.
    """
    _require_simulation()

    if sim_state.config is None:
        raise HTTPException(status_code=503, detail="Configuration not available.")

    save_path = Path(sim_state.config.save_path)
    state_file = save_path / "world_state.json"

    if not state_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No snapshot file found at {state_file}.",
        )

    try:
        from src.engine.persistence import load_state
        loaded = load_state(save_path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load snapshot: {exc}",
        )

    # The simulation overwrites a single snapshot file. If the saved
    # tick is later than the requested tick, we cannot serve the request.
    if loaded.tick > tick:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Requested tick {tick} but the only available snapshot is "
                f"from tick {loaded.tick} (later). Per-tick snapshots are not retained."
            ),
        )

    return world_state_to_response(loaded)


# ---------------------------------------------------------------------------
# WebSocket — live event stream
# ---------------------------------------------------------------------------

@router.websocket("/api/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live simulation event streaming.

    After connecting, clients receive all BusEvents as JSON. Clients
    can send a subscription filter message to restrict event types:

        {"subscribe": ["AGENT_MOVED", "MESSAGE_SENT"]}

    An empty list resets to receiving all events.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if isinstance(data, dict) and "subscribe" in data:
                await manager.handle_subscription(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
