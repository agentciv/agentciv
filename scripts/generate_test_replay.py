#!/usr/bin/env python3
"""Generate synthetic replay data for testing the frontend replay engine.

Creates a small fake simulation (5 agents, 20 ticks) with realistic-looking
data so the replay engine can be tested without running a real simulation.

Usage:
    python3 scripts/generate_test_replay.py
    # Then: cd src/frontend && npm run dev
    # Visit http://localhost:5173/fishbowl
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
from pathlib import Path

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

OUTPUT_DIR = Path(_PROJECT_ROOT) / "src" / "frontend" / "public" / "replay_data"
GRID_W = 20
GRID_H = 20
NUM_AGENTS = 5
NUM_TICKS = 20
CHUNK_SIZE = 50  # all fits in one chunk for test


def make_tile(x: int, y: int) -> dict:
    terrains = ["plains", "plains", "plains", "rocky", "dense"]
    terrain = random.choice(terrains)
    resources: dict[str, dict] = {}
    for rtype in ["food", "water", "material"]:
        amt = random.uniform(0, 10)
        resources[rtype] = {
            "resource_type": rtype,
            "amount": round(amt, 2),
            "max_amount": 10.0,
            "regeneration_rate": 0.1,
            "gathering_pressure": 0.0,
        }
    return {
        "position": {"x": x, "y": y},
        "terrain": terrain,
        "resources": resources,
        "structures": [],
    }


def make_agent(agent_id: int, tick: int) -> dict:
    return {
        "id": agent_id,
        "position": {
            "x": random.randint(2, GRID_W - 3),
            "y": random.randint(2, GRID_H - 3),
        },
        "needs": {
            "levels": {
                "food": round(random.uniform(0.6, 1.0), 2),
                "water": round(random.uniform(0.6, 1.0), 2),
                "material": round(random.uniform(0.4, 1.0), 2),
            }
        },
        "wellbeing": round(random.uniform(0.3, 0.8), 2),
        "curiosity": round(random.uniform(0.3, 0.7), 2),
        "capabilities": {
            "perception_range": 5,
            "movement_speed": 1.0,
            "memory_capacity": 50,
            "base_perception_range": 5,
            "base_movement_speed": 1.0,
            "base_memory_capacity": 50,
        },
        "memories": [
            {"tick": max(0, tick - 1), "summary": "Gathered food nearby", "importance": 0.5, "access_count": 1},
        ],
        "age": tick,
        "alive_since_tick": 0,
        "current_action": {
            "type": random.choice(["move", "gather", "communicate", "wait"]),
            "direction": [1, 0] if random.random() > 0.5 else [0, 1],
            "resource_type": "food",
            "message": None,
            "target_agent_id": None,
            "goal": "survive and explore",
            "plan_steps": [],
            "structure_type": None,
            "marker_message": None,
            "compose_targets": None,
            "innovation_description": None,
            "rule_text": None,
            "rule_id": None,
            "reasoning": "I need to find resources",
        },
        "goals": ["find food", "explore the world"],
        "plan": ["move east", "gather food"],
        "current_routine": None,
        "inventory": random.choices(["food", "water", "material"], k=random.randint(0, 3)),
        "interactions_this_tick": [],
        "agents_in_perception": [],
        "known_resources": {},
        "activity_counts": {"gather": tick * 2, "move": tick * 3},
        "specialisations": ["gather"] if agent_id == 0 and tick > 10 else [],
        "known_recipes": [],
        "visited_tiles": [[random.randint(0, GRID_W - 1), random.randint(0, GRID_H - 1)] for _ in range(min(tick * 2, 10))],
        "met_agents": [a for a in range(NUM_AGENTS) if a != agent_id and random.random() > 0.5],
        "relationships": {
            str(a): {
                "interaction_count": random.randint(1, tick + 1),
                "positive_count": random.randint(0, tick + 1),
                "negative_count": 0,
                "last_interaction_tick": max(0, tick - random.randint(0, 3)),
                "is_bonded": tick > 8 and random.random() > 0.6,
            }
            for a in range(NUM_AGENTS)
            if a != agent_id and random.random() > 0.4
        },
    }


def make_snapshot(tick: int, agents_state: dict[int, dict]) -> dict:
    tiles = [
        [make_tile(x, y) for y in range(GRID_H)]
        for x in range(GRID_W)
    ]

    # Add a structure after tick 8
    if tick >= 8:
        tiles[5][5]["structures"].append({
            "structure_type": "shelter",
            "builder_id": 0,
            "built_tick": 8,
            "health": 1.0,
            "message": None,
            "stored_resources": {},
            "capacity": 10.0,
            "custom_name": None,
            "custom_description": None,
            "composed_from": None,
        })

    # Move agents slightly each tick
    for aid, agent in agents_state.items():
        dx = random.choice([-1, 0, 0, 1])
        dy = random.choice([-1, 0, 0, 1])
        agent["position"]["x"] = max(0, min(GRID_W - 1, agent["position"]["x"] + dx))
        agent["position"]["y"] = max(0, min(GRID_H - 1, agent["position"]["y"] + dy))
        agent["age"] = tick
        agent["needs"]["levels"]["food"] = max(0.35, agent["needs"]["levels"]["food"] - 0.01)
        agent["needs"]["levels"]["water"] = max(0.35, agent["needs"]["levels"]["water"] - 0.01)
        agent["wellbeing"] = round(0.3 + 0.4 * math.sin(tick * 0.3 + aid), 2)

    return {
        "tick": tick,
        "grid_width": GRID_W,
        "grid_height": GRID_H,
        "tiles": tiles,
        "agents": {str(aid): dict(a) for aid, a in agents_state.items()},
        "next_agent_id": NUM_AGENTS,
        "discovered_recipes": [],
        "collective_rules": [],
        "next_rule_id": 0,
    }


def make_events(tick: int) -> list[dict]:
    events: list[dict] = []
    ts = 1000000 + tick * 5000

    # tick_start
    events.append({
        "type": "tick_start",
        "tick": tick,
        "timestamp": ts,
        "agent_id": None,
        "data": {},
    })

    # Some agent events
    for aid in range(NUM_AGENTS):
        if random.random() > 0.5:
            events.append({
                "type": "reasoning_step",
                "tick": tick,
                "timestamp": ts + aid * 100,
                "agent_id": aid,
                "data": {
                    "response": random.choice([
                        "I should look for food nearby. My hunger is getting low.",
                        "There are other entities to the east. Should I approach?",
                        "I notice resources are depleting here. Time to move.",
                        "I want to build something. I have enough materials.",
                        "The world is vast. I wonder what lies beyond my perception.",
                    ]),
                },
            })

        if random.random() > 0.6:
            events.append({
                "type": "action_taken",
                "tick": tick,
                "timestamp": ts + aid * 100 + 50,
                "agent_id": aid,
                "data": {
                    "action": random.choice(["move", "gather", "communicate", "wait"]),
                    "reasoning": "Pursuing my current goal",
                },
            })

    # Occasional messages
    if tick % 3 == 0 and NUM_AGENTS >= 2:
        sender = random.randint(0, NUM_AGENTS - 1)
        receiver = (sender + 1) % NUM_AGENTS
        events.append({
            "type": "message_sent",
            "tick": tick,
            "timestamp": ts + 2000,
            "agent_id": sender,
            "data": {
                "sender_id": sender,
                "receiver_id": receiver,
                "content": random.choice([
                    "I found food to the north.",
                    "Watch out, resources are scarce here.",
                    "Shall we build something together?",
                    "I've been exploring the western edge.",
                ]),
            },
        })

    # Structure built event at tick 8
    if tick == 8:
        events.append({
            "type": "structure_built",
            "tick": tick,
            "timestamp": ts + 3000,
            "agent_id": 0,
            "data": {
                "structure_type": "shelter",
                "position": {"x": 5, "y": 5},
            },
        })

    # Specialisation at tick 12
    if tick == 12:
        events.append({
            "type": "specialisation_gained",
            "tick": tick,
            "timestamp": ts + 4000,
            "agent_id": 0,
            "data": {
                "activity": "gather",
                "count": 24,
            },
        })

    # Watcher tick report (per-tick chronicle entry)
    communicating = sum(1 for _ in events if _.get("type") == "message_sent")
    events.append({
        "type": "watcher_tick_report",
        "tick": tick,
        "timestamp": ts + 4500,
        "agent_id": None,
        "data": {
            "population": {
                "total": NUM_AGENTS,
                "healthy": NUM_AGENTS - (1 if tick > 15 else 0),
                "degraded": 1 if tick > 15 else 0,
            },
            "communication": {
                "messages_sent": communicating,
            },
            "structures": {
                "total": 1 if tick >= 8 else 0,
            },
        },
    })

    # Watcher milestones at key moments
    if tick == 0:
        events.append({
            "type": "watcher_milestone",
            "tick": tick,
            "timestamp": ts + 4600,
            "agent_id": None,
            "data": {
                "name": "Civilisation begins",
                "commentary": f"{NUM_AGENTS} agents placed in a {GRID_W}\u00d7{GRID_H} world. No instructions given.",
            },
        })
    if tick == 3:
        events.append({
            "type": "watcher_milestone",
            "tick": tick,
            "timestamp": ts + 4600,
            "agent_id": None,
            "data": {
                "name": "First contact",
                "commentary": "Two agents communicate for the first time. Neither was told to.",
            },
        })
    if tick == 8:
        events.append({
            "type": "watcher_milestone",
            "tick": tick,
            "timestamp": ts + 4600,
            "agent_id": None,
            "data": {
                "name": "First structure",
                "commentary": "Agent 0 builds the first shelter. A permanent mark on the world.",
            },
        })
    if tick == 12:
        events.append({
            "type": "watcher_milestone",
            "tick": tick,
            "timestamp": ts + 4600,
            "agent_id": None,
            "data": {
                "name": "First specialisation",
                "commentary": "Agent 0 develops gathering expertise through repeated practice.",
            },
        })

    # tick_end
    events.append({
        "type": "tick_end",
        "tick": tick,
        "timestamp": ts + 5000,
        "agent_id": None,
        "data": {},
    })

    return events


def main() -> None:
    random.seed(42)
    print(f"Generating synthetic replay data: {NUM_AGENTS} agents, {NUM_TICKS} ticks")
    print(f"Output: {OUTPUT_DIR}")

    # Create directories
    (OUTPUT_DIR / "snapshots").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "events").mkdir(parents=True, exist_ok=True)

    # Generate agent initial state
    agents_state: dict[int, dict] = {}
    for aid in range(NUM_AGENTS):
        agents_state[aid] = make_agent(aid, 0)

    # Generate per-tick snapshots and events
    all_snapshots: dict[str, dict] = {}
    all_events: list[dict] = []

    for tick in range(NUM_TICKS):
        snapshot = make_snapshot(tick, agents_state)
        all_snapshots[str(tick)] = snapshot
        all_events.extend(make_events(tick))

    # Write single chunk (all ticks fit in one for test data)
    chunk_name = f"chunk_000_{NUM_TICKS - 1:03d}"

    with open(OUTPUT_DIR / "snapshots" / f"{chunk_name}.json", "w") as f:
        json.dump(all_snapshots, f, separators=(",", ":"))

    with open(OUTPUT_DIR / "events" / f"{chunk_name}.json", "w") as f:
        json.dump(all_events, f, separators=(",", ":"))

    # Chronicle (empty for test)
    with open(OUTPUT_DIR / "chronicle.json", "w") as f:
        json.dump([], f)

    # Messages
    messages = [e for e in all_events if e["type"] == "message_sent"]
    with open(OUTPUT_DIR / "messages.json", "w") as f:
        json.dump(messages, f, separators=(",", ":"))

    # Metadata
    metadata = {
        "name": "Test Civilisation",
        "min_tick": 0,
        "max_tick": NUM_TICKS - 1,
        "total_ticks": NUM_TICKS,
        "agent_count": NUM_AGENTS,
        "grid_width": GRID_W,
        "grid_height": GRID_H,
        "total_events": len(all_events),
        "total_messages": len(messages),
        "total_chronicle_entries": 0,
        "chunk_size": CHUNK_SIZE,
        "snapshot_chunks": [{
            "name": chunk_name,
            "start_tick": 0,
            "end_tick": NUM_TICKS - 1,
            "snapshot_count": NUM_TICKS,
            "file": f"snapshots/{chunk_name}.json",
        }],
        "event_chunks": [{
            "name": chunk_name,
            "start_tick": 0,
            "end_tick": NUM_TICKS - 1,
            "event_count": len(all_events),
            "file": f"events/{chunk_name}.json",
        }],
    }

    with open(OUTPUT_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob("*.json"))
    print(f"\nGenerated:")
    print(f"  {NUM_TICKS} tick snapshots")
    print(f"  {len(all_events)} events")
    print(f"  {len(messages)} messages")
    print(f"  Total size: {total_size / 1024:.1f} KB")
    print(f"\nTo test: cd src/frontend && npm run dev → visit /fishbowl")


if __name__ == "__main__":
    main()
