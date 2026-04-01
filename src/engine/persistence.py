"""State save/load for Agent Civilisation.

Serialises and deserialises the full WorldState (including all agents,
tiles, resources, memories, events, and messages) to JSON files.

Event and message logs are written to append-mode files so they grow
unbounded without inflating the state snapshot.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.types import (
    Action,
    ActionType,
    AgentState,
    BusEvent,
    BusEventType,
    Capabilities,
    CollectiveRule,
    DiscoveredRecipe,
    Event,
    EventType,
    MemoryEntry,
    Message,
    NeedsState,
    Position,
    RelationshipRecord,
    Resource,
    Structure,
    StructureType,
    TerrainType,
    Tile,
    WorldState,
)


# ======================================================================
# Custom JSON encoder
# ======================================================================

class SimulationEncoder(json.JSONEncoder):
    """Encode simulation dataclasses to JSON-serialisable dicts."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Position):
            return {"x": obj.x, "y": obj.y}

        if isinstance(obj, Resource):
            return {
                "resource_type": obj.resource_type,
                "amount": obj.amount,
                "max_amount": obj.max_amount,
                "regeneration_rate": obj.regeneration_rate,
                "gathering_pressure": obj.gathering_pressure,
            }

        if isinstance(obj, Structure):
            return {
                "structure_type": obj.structure_type.value,
                "builder_id": obj.builder_id,
                "built_tick": obj.built_tick,
                "health": obj.health,
                "message": obj.message,
                "stored_resources": obj.stored_resources,
                "capacity": obj.capacity,
                "custom_name": obj.custom_name,
                "custom_description": obj.custom_description,
                "composed_from": obj.composed_from,
            }

        if isinstance(obj, Tile):
            return {
                "position": self.default(obj.position),
                "terrain": obj.terrain.value,
                "resources": {k: self.default(v) for k, v in obj.resources.items()},
                "structures": [self.default(s) for s in obj.structures],
            }

        if isinstance(obj, Capabilities):
            return {
                "perception_range": obj.perception_range,
                "movement_speed": obj.movement_speed,
                "memory_capacity": obj.memory_capacity,
                "base_perception_range": obj.base_perception_range,
                "base_movement_speed": obj.base_movement_speed,
                "base_memory_capacity": obj.base_memory_capacity,
            }

        if isinstance(obj, NeedsState):
            return {"levels": obj.levels}

        if isinstance(obj, MemoryEntry):
            return {
                "tick": obj.tick,
                "summary": obj.summary,
                "importance": obj.importance,
                "access_count": obj.access_count,
            }

        if isinstance(obj, Action):
            return {
                "type": obj.type.value,
                "direction": list(obj.direction) if obj.direction else None,
                "resource_type": obj.resource_type,
                "message": obj.message,
                "target_agent_id": obj.target_agent_id,
                "goal": obj.goal,
                "plan_steps": obj.plan_steps,
                "structure_type": obj.structure_type,
                "marker_message": obj.marker_message,
                "compose_targets": obj.compose_targets,
                "innovation_description": obj.innovation_description,
                "rule_text": obj.rule_text,
                "rule_id": obj.rule_id,
                "reasoning": obj.reasoning,
            }

        if isinstance(obj, Event):
            return {
                "type": obj.type.value,
                "tick": obj.tick,
                "agent_id": obj.agent_id,
                "data": obj.data,
            }

        if isinstance(obj, Message):
            return {
                "sender_id": obj.sender_id,
                "receiver_id": obj.receiver_id,
                "content": obj.content,
                "tick": obj.tick,
            }

        if isinstance(obj, AgentState):
            return {
                "id": obj.id,
                "position": self.default(obj.position),
                "needs": self.default(obj.needs),
                "wellbeing": obj.wellbeing,
                "curiosity": obj.curiosity,
                "capabilities": self.default(obj.capabilities),
                "memories": [self.default(m) for m in obj.memories],
                "age": obj.age,
                "alive_since_tick": obj.alive_since_tick,
                "current_action": self.default(obj.current_action) if obj.current_action else None,
                "goals": obj.goals,
                "plan": obj.plan,
                "current_routine": obj.current_routine,
                "inventory": obj.inventory,
                "interactions_this_tick": obj.interactions_this_tick,
                "agents_in_perception": list(obj.agents_in_perception),
                "known_resources": {
                    f"{k[0]},{k[1]}": v for k, v in obj.known_resources.items()
                },
                "activity_counts": obj.activity_counts,
                "specialisations": obj.specialisations,
                "known_recipes": obj.known_recipes,
                "visited_tiles": [list(t) for t in obj.visited_tiles],
                "met_agents": list(obj.met_agents),
                "relationships": {
                    str(aid): {
                        "interaction_count": rel.interaction_count,
                        "positive_count": rel.positive_count,
                        "negative_count": rel.negative_count,
                        "last_interaction_tick": rel.last_interaction_tick,
                        "is_bonded": rel.is_bonded,
                    }
                    for aid, rel in obj.relationships.items()
                },
                # Maslow drive tracking
                "ticks_survival_stable": obj.ticks_survival_stable,
                "structures_built_count": obj.structures_built_count,
                "innovations_proposed": obj.innovations_proposed,
                "rules_established_count": obj.rules_established_count,
                "recent_actions": obj.recent_actions,
                "maslow_level": obj.maslow_level,
            }

        if isinstance(obj, DiscoveredRecipe):
            return {
                "inputs": obj.inputs,
                "output_name": obj.output_name,
                "output_description": obj.output_description,
                "discovered_by": obj.discovered_by,
                "discovered_tick": obj.discovered_tick,
                "times_built": obj.times_built,
                "effect_type": obj.effect_type,
            }

        if isinstance(obj, CollectiveRule):
            return {
                "rule_id": obj.rule_id,
                "text": obj.text,
                "proposed_by": obj.proposed_by,
                "proposed_tick": obj.proposed_tick,
                "accepted_by": obj.accepted_by,
                "ignored_by": obj.ignored_by,
                "established": obj.established,
            }

        if isinstance(obj, WorldState):
            return {
                "tick": obj.tick,
                "grid_width": obj.grid_width,
                "grid_height": obj.grid_height,
                "tiles": [
                    [self.default(obj.tiles[x][y]) for y in range(obj.grid_height)]
                    for x in range(obj.grid_width)
                ],
                "agents": {
                    str(aid): self.default(agent)
                    for aid, agent in obj.agents.items()
                },
                "next_agent_id": obj.next_agent_id,
                "discovered_recipes": [self.default(r) for r in obj.discovered_recipes],
                "collective_rules": [self.default(r) for r in obj.collective_rules],
                "next_rule_id": obj.next_rule_id,
            }

        if isinstance(obj, set):
            return list(obj)

        return super().default(obj)


# ======================================================================
# Decoders — reconstruct dataclasses from dicts
# ======================================================================

def _decode_position(d: dict) -> Position:
    return Position(x=d["x"], y=d["y"])


def _decode_resource(d: dict) -> Resource:
    return Resource(
        resource_type=d["resource_type"],
        amount=d["amount"],
        max_amount=d["max_amount"],
        regeneration_rate=d["regeneration_rate"],
        gathering_pressure=d.get("gathering_pressure", 0.0),
    )


def _decode_structure(d: dict) -> Structure:
    return Structure(
        structure_type=StructureType(d["structure_type"]),
        builder_id=d["builder_id"],
        built_tick=d["built_tick"],
        health=d.get("health", 1.0),
        message=d.get("message"),
        stored_resources=d.get("stored_resources", {}),
        capacity=d.get("capacity", 10.0),
        custom_name=d.get("custom_name"),
        custom_description=d.get("custom_description"),
        composed_from=d.get("composed_from"),
    )


def _decode_tile(d: dict) -> Tile:
    return Tile(
        position=_decode_position(d["position"]),
        terrain=TerrainType(d["terrain"]),
        resources={k: _decode_resource(v) for k, v in d["resources"].items()},
        structures=[_decode_structure(s) for s in d.get("structures", [])],
    )


def _decode_capabilities(d: dict) -> Capabilities:
    return Capabilities(
        perception_range=d["perception_range"],
        movement_speed=d["movement_speed"],
        memory_capacity=d["memory_capacity"],
        base_perception_range=d["base_perception_range"],
        base_movement_speed=d["base_movement_speed"],
        base_memory_capacity=d["base_memory_capacity"],
    )


def _decode_needs(d: dict) -> NeedsState:
    return NeedsState(levels=d["levels"])


def _decode_memory_entry(d: dict) -> MemoryEntry:
    return MemoryEntry(
        tick=d["tick"],
        summary=d["summary"],
        importance=d.get("importance", 0.5),
        access_count=d.get("access_count", 0),
    )


def _decode_action(d: dict | None) -> Action | None:
    if d is None:
        return None
    return Action(
        type=ActionType(d["type"]),
        direction=tuple(d["direction"]) if d.get("direction") else None,
        resource_type=d.get("resource_type"),
        message=d.get("message"),
        target_agent_id=d.get("target_agent_id"),
        goal=d.get("goal"),
        plan_steps=d.get("plan_steps"),
        structure_type=d.get("structure_type"),
        marker_message=d.get("marker_message"),
        compose_targets=d.get("compose_targets"),
        innovation_description=d.get("innovation_description"),
        rule_text=d.get("rule_text"),
        rule_id=d.get("rule_id"),
        reasoning=d.get("reasoning", ""),
    )


def _decode_agent(d: dict) -> AgentState:
    # Decode known_resources: "x,y" -> (x, y)
    known_res: dict[tuple[int, int], str] = {}
    for key, val in d.get("known_resources", {}).items():
        parts = key.split(",")
        known_res[(int(parts[0]), int(parts[1]))] = val

    return AgentState(
        id=d["id"],
        position=_decode_position(d["position"]),
        needs=_decode_needs(d["needs"]),
        wellbeing=d["wellbeing"],
        curiosity=d.get("curiosity", 0.5),
        capabilities=_decode_capabilities(d["capabilities"]),
        memories=[_decode_memory_entry(m) for m in d.get("memories", [])],
        age=d.get("age", 0),
        alive_since_tick=d.get("alive_since_tick", 0),
        current_action=_decode_action(d.get("current_action")),
        goals=d.get("goals", []),
        plan=d.get("plan", []),
        current_routine=d.get("current_routine"),
        inventory=d.get("inventory", []),
        interactions_this_tick=d.get("interactions_this_tick", []),
        agents_in_perception=set(d.get("agents_in_perception", [])),
        known_resources=known_res,
        activity_counts=d.get("activity_counts", {}),
        specialisations=d.get("specialisations", []),
        known_recipes=d.get("known_recipes", []),
        visited_tiles={tuple(t) for t in d.get("visited_tiles", [])},
        met_agents=set(d.get("met_agents", [])),
        relationships={
            int(aid): RelationshipRecord(
                interaction_count=rel.get("interaction_count", 0),
                positive_count=rel.get("positive_count", 0),
                negative_count=rel.get("negative_count", 0),
                last_interaction_tick=rel.get("last_interaction_tick", 0),
                is_bonded=rel.get("is_bonded", False),
            )
            for aid, rel in d.get("relationships", {}).items()
        },
        # Maslow drive tracking
        ticks_survival_stable=d.get("ticks_survival_stable", 0),
        structures_built_count=d.get("structures_built_count", 0),
        innovations_proposed=d.get("innovations_proposed", []),
        rules_established_count=d.get("rules_established_count", 0),
        recent_actions=d.get("recent_actions", []),
        maslow_level=d.get("maslow_level", 1),
    )


def _decode_event(d: dict) -> Event:
    return Event(
        type=EventType(d["type"]),
        tick=d["tick"],
        agent_id=d["agent_id"],
        data=d.get("data", {}),
    )


def _decode_message(d: dict) -> Message:
    return Message(
        sender_id=d["sender_id"],
        receiver_id=d["receiver_id"],
        content=d["content"],
        tick=d["tick"],
    )


def _decode_discovered_recipe(d: dict) -> DiscoveredRecipe:
    return DiscoveredRecipe(
        inputs=d["inputs"],
        output_name=d["output_name"],
        output_description=d["output_description"],
        discovered_by=d["discovered_by"],
        discovered_tick=d["discovered_tick"],
        times_built=d.get("times_built", 0),
        effect_type=d.get("effect_type", "marker"),
    )


def _decode_collective_rule(d: dict) -> CollectiveRule:
    return CollectiveRule(
        rule_id=d["rule_id"],
        text=d["text"],
        proposed_by=d["proposed_by"],
        proposed_tick=d["proposed_tick"],
        accepted_by=d.get("accepted_by", []),
        ignored_by=d.get("ignored_by", []),
        established=d.get("established", False),
    )


def _decode_world_state(d: dict) -> WorldState:
    width = d["grid_width"]
    height = d["grid_height"]

    tiles: list[list[Tile]] = [
        [_decode_tile(d["tiles"][x][y]) for y in range(height)]
        for x in range(width)
    ]

    agents: dict[int, AgentState] = {
        int(aid): _decode_agent(adata) for aid, adata in d["agents"].items()
    }

    return WorldState(
        tick=d["tick"],
        grid_width=width,
        grid_height=height,
        tiles=tiles,
        agents=agents,
        next_agent_id=d["next_agent_id"],
        discovered_recipes=[
            _decode_discovered_recipe(r)
            for r in d.get("discovered_recipes", [])
        ],
        collective_rules=[
            _decode_collective_rule(r)
            for r in d.get("collective_rules", [])
        ],
        next_rule_id=d.get("next_rule_id", 0),
    )


# ======================================================================
# Public API
# ======================================================================

def save_state(world_state: WorldState, path: str | Path) -> None:
    """Save the full WorldState to a JSON file.

    Uses atomic write (temp file + rename) to prevent corruption
    if the process crashes mid-save. Creates parent directories if needed.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    encoder = SimulationEncoder()
    data = encoder.default(world_state)

    target = path / "world_state.json"
    tmp = path / "world_state.json.tmp"

    with open(tmp, "w") as f:
        json.dump(data, f, cls=SimulationEncoder, indent=2)
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp, target)


def save_tick_snapshot(world_state: WorldState, path: str | Path) -> None:
    """Save a per-tick snapshot for replay recording.

    Saves to snapshots/tick_NNNN.json within the given directory.
    Uses compact JSON (no indent) to minimise file size.
    """
    path = Path(path) / "snapshots"
    path.mkdir(parents=True, exist_ok=True)

    tick = world_state.tick
    target = path / f"tick_{tick:04d}.json"
    tmp = path / f"tick_{tick:04d}.json.tmp"

    encoder = SimulationEncoder()
    data = encoder.default(world_state)

    with open(tmp, "w") as f:
        json.dump(data, f, cls=SimulationEncoder)
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp, target)


def load_state(path: str | Path) -> WorldState:
    """Load a WorldState from a previously saved JSON file."""
    path = Path(path)
    state_file = path / "world_state.json"
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")

    with open(state_file) as f:
        data = json.load(f)

    return _decode_world_state(data)


def append_events(events: list[Event], log_path: str | Path) -> None:
    """Append events to the event log file (one JSON object per line)."""
    log_path = Path(log_path)
    log_path.mkdir(parents=True, exist_ok=True)
    event_file = log_path / "events.jsonl"

    encoder = SimulationEncoder()
    with open(event_file, "a") as f:
        for event in events:
            line = json.dumps(encoder.default(event))
            f.write(line + "\n")


def append_messages(messages: list[Message], log_path: str | Path) -> None:
    """Append messages to the message log file (one JSON object per line)."""
    log_path = Path(log_path)
    log_path.mkdir(parents=True, exist_ok=True)
    msg_file = log_path / "messages.jsonl"

    encoder = SimulationEncoder()
    with open(msg_file, "a") as f:
        for msg in messages:
            line = json.dumps(encoder.default(msg))
            f.write(line + "\n")


def append_bus_events(bus_events: list[BusEvent], log_path: str | Path) -> None:
    """Append bus events to the bus event log file (one JSON object per line).

    Bus events carry richer data than Event objects — reasoning traces,
    observations, watcher reports, etc. These power the replay feed.
    """
    log_path = Path(log_path)
    log_path.mkdir(parents=True, exist_ok=True)
    bus_file = log_path / "bus_events.jsonl"

    with open(bus_file, "a") as f:
        for event in bus_events:
            line = json.dumps({
                "type": event.type.value,
                "tick": event.tick,
                "timestamp": event.timestamp,
                "agent_id": event.agent_id,
                "data": event.data,
            })
            f.write(line + "\n")


def load_events(log_path: str | Path) -> list[Event]:
    """Load all events from the event log."""
    event_file = Path(log_path) / "events.jsonl"
    if not event_file.exists():
        return []
    events: list[Event] = []
    with open(event_file) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(_decode_event(json.loads(line)))
    return events


def load_messages(log_path: str | Path) -> list[Message]:
    """Load all messages from the message log."""
    msg_file = Path(log_path) / "messages.jsonl"
    if not msg_file.exists():
        return []
    messages: list[Message] = []
    with open(msg_file) as f:
        for line in f:
            line = line.strip()
            if line:
                messages.append(_decode_message(json.loads(line)))
    return messages
