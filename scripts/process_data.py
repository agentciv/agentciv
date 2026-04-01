#!/usr/bin/env python3
"""
AgentCiv Data Processing Pipeline
Phase 2: Process simulation data for website fishbowl replay and paper figures.

Produces:
  data/exports/replay/     — tick-by-tick replay data for fishbowl engine
  data/exports/stats/      — summary statistics and chart data
  data/exports/manifest.json — data manifest for website build

Usage:
  python3 scripts/process_data.py
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict, Counter

# === PATHS ===
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SIM_DIR = DATA_DIR / "simulation_state"
SNAP_DIR = SIM_DIR / "snapshots"
EXPORT_DIR = DATA_DIR / "exports"
REPLAY_DIR = EXPORT_DIR / "replay"
STATS_DIR = EXPORT_DIR / "stats"
INTERVIEWS_DIR = DATA_DIR / "interviews"

TOTAL_TICKS = 70  # 0-70 inclusive = 71 snapshots


def ensure_dirs():
    """Create export directories."""
    for d in [EXPORT_DIR, REPLAY_DIR, STATS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    print(f"Export directories ready: {EXPORT_DIR}")


def load_snapshot(tick: int) -> dict:
    """Load a single tick snapshot."""
    path = SNAP_DIR / f"tick_{tick:04d}.json"
    with open(path, "r") as f:
        return json.load(f)


def load_jsonl(filename: str) -> list:
    """Load a JSONL file from simulation_state."""
    path = SIM_DIR / filename
    if not path.exists():
        print(f"  Warning: {filename} not found, skipping")
        return []
    entries = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def load_all_snapshots() -> dict:
    """Load all 71 snapshots. Returns {tick: snapshot}."""
    print("Loading snapshots...")
    snapshots = {}
    for tick in range(TOTAL_TICKS + 1):
        snapshots[tick] = load_snapshot(tick)
    print(f"  Loaded {len(snapshots)} snapshots (tick 0-{TOTAL_TICKS})")
    return snapshots


# ============================================================
# 2.1 — REPLAY DATA (for fishbowl engine)
# ============================================================

def extract_replay_tick(snap: dict, tick_messages: list, tick_bus_events: list) -> dict:
    """Extract compact replay data for a single tick."""
    tick = snap["tick"]

    # Agent states (compact)
    agents = {}
    for aid, agent in snap["agents"].items():
        agents[aid] = {
            "id": agent["id"],
            "pos": [agent["position"]["x"], agent["position"]["y"]],
            "wellbeing": round(agent["wellbeing"], 3),
            "maslow": agent.get("maslow_level", 1),
            "needs": {
                "water": round(agent["needs"]["levels"].get("water", 0), 3),
                "food": round(agent["needs"]["levels"].get("food", 0), 3),
                "material": round(agent["needs"]["levels"].get("material", 0), 3),
            },
            "inventory": agent.get("inventory", []),
            "specialisations": agent.get("specialisations", []),
            "structures_built": agent.get("structures_built_count", 0),
            "known_recipes": agent.get("known_recipes", []),
            "goals": agent.get("goals", [])[:3],  # top 3 goals
        }

        # Add relationship summary
        rels = agent.get("relationships", {})
        if rels:
            agents[aid]["bonds"] = [
                int(pid) for pid, r in rels.items() if r.get("is_bonded")
            ]
            agents[aid]["relationship_count"] = len(rels)

        # Activity counts for specialisation depth
        activity = agent.get("activity_counts", {})
        if activity:
            agents[aid]["activity_counts"] = {
                k: v for k, v in activity.items() if v > 0
            }

    # Structures (compact)
    structures = []
    for row in snap.get("tiles", []):
        for tile in row:
            for s in tile.get("structures", []):
                structures.append({
                    "pos": [tile["position"]["x"], tile["position"]["y"]],
                    "type": s["structure_type"],
                    "builder": s["builder_id"],
                    "tick": s["built_tick"],
                    "health": round(s["health"], 2),
                    "name": s.get("custom_name", ""),
                    "desc": s.get("custom_description", ""),
                })

    # Resources (grid summary — average levels)
    resource_totals = {"water": 0, "food": 0, "material": 0}
    resource_counts = {"water": 0, "food": 0, "material": 0}
    for row in snap.get("tiles", []):
        for tile in row:
            for rtype, rdata in tile.get("resources", {}).items():
                if rtype in resource_totals:
                    resource_totals[rtype] += rdata.get("amount", 0)
                    resource_counts[rtype] += 1

    avg_resources = {}
    for rtype in resource_totals:
        if resource_counts[rtype] > 0:
            avg_resources[rtype] = round(
                resource_totals[rtype] / resource_counts[rtype], 3
            )

    # Messages this tick
    messages = [
        {
            "from": m["sender_id"],
            "to": m["receiver_id"],
            "text": m["content"][:200],  # truncate for replay
        }
        for m in tick_messages
    ]

    # Key events this tick (from bus_events)
    events = []
    for e in tick_bus_events:
        etype = e.get("type", "")
        if etype in (
            "structure_built", "innovation_succeeded", "innovation_failed",
            "specialisation_gained", "rule_proposed", "rule_accepted",
            "rule_established", "bond_formed", "recipe_discovered",
            "composition_succeeded",
        ):
            event = {"type": etype, "agent": e.get("agent_id")}
            edata = e.get("data", {})
            if etype == "structure_built":
                event["structure_type"] = edata.get("structure_type", "")
                event["position"] = edata.get("position")
            elif etype == "innovation_succeeded":
                event["name"] = edata.get("name", "")
                event["description"] = edata.get("description", "")
            elif etype == "specialisation_gained":
                event["skill"] = edata.get("skill", edata.get("specialisation", ""))
                event["tier"] = edata.get("tier", "")
            elif etype == "rule_accepted":
                event["rule_text"] = edata.get("rule_text", "")[:100]
            elif etype == "recipe_discovered":
                event["recipe_name"] = edata.get("output_name", "")
            events.append(event)

    # Recipes and rules
    recipes = [
        {
            "name": r["output_name"],
            "desc": r.get("output_description", ""),
            "by": r["discovered_by"],
            "tick": r["discovered_tick"],
            "times_built": r.get("times_built", 0),
            "effect": r.get("effect_type", ""),
        }
        for r in snap.get("discovered_recipes", [])
    ]

    rules = [
        {
            "id": r["rule_id"],
            "text": r["text"],
            "by": r["proposed_by"],
            "tick": r["proposed_tick"],
            "accepted": r.get("accepted_by", []),
            "established": r.get("established", False),
        }
        for r in snap.get("collective_rules", [])
    ]

    return {
        "tick": tick,
        "agents": agents,
        "structures": structures,
        "structure_count": len(structures),
        "resources_avg": avg_resources,
        "messages": messages,
        "message_count": len(messages),
        "events": events,
        "recipes": recipes,
        "recipe_count": len(recipes),
        "rules": rules,
    }


def build_replay_data(snapshots: dict, messages: list, bus_events: list):
    """Build complete replay dataset."""
    print("\nBuilding replay data...")

    # Group messages and events by tick
    msgs_by_tick = defaultdict(list)
    for m in messages:
        msgs_by_tick[m["tick"]].append(m)

    events_by_tick = defaultdict(list)
    for e in bus_events:
        events_by_tick[e.get("tick", -1)].append(e)

    # Build per-tick replay frames
    timeline = []
    for tick in range(TOTAL_TICKS + 1):
        snap = snapshots[tick]
        frame = extract_replay_tick(
            snap,
            msgs_by_tick.get(tick, []),
            events_by_tick.get(tick, []),
        )
        timeline.append(frame)

    # Metadata
    meta = {
        "total_ticks": TOTAL_TICKS,
        "grid_width": snapshots[0]["grid_width"],
        "grid_height": snapshots[0]["grid_height"],
        "agent_count": len(snapshots[0]["agents"]),
        "agent_ids": sorted(int(k) for k in snapshots[0]["agents"].keys()),
        "total_messages": len(messages),
        "total_structures": timeline[-1]["structure_count"],
        "total_recipes": timeline[-1]["recipe_count"],
        "eras": {
            "survival_trap": {"start": 0, "end": 50, "label": "Era I: Survival Trap"},
            "emergence_explosion": {"start": 50, "end": 60, "label": "Era II: Emergence Explosion"},
            "sustained_flourishing": {"start": 60, "end": 70, "label": "Era III: Sustained Flourishing"},
        },
        "upgrade_tick": 50,
    }

    # Save chunked (per-tick files for lazy loading)
    chunks_dir = REPLAY_DIR / "ticks"
    chunks_dir.mkdir(exist_ok=True)
    for frame in timeline:
        tick = frame["tick"]
        with open(chunks_dir / f"tick_{tick:04d}.json", "w") as f:
            json.dump(frame, f, separators=(",", ":"))

    # Save complete timeline (single file for small sims)
    with open(REPLAY_DIR / "timeline.json", "w") as f:
        json.dump(timeline, f, separators=(",", ":"))

    # Save metadata
    with open(REPLAY_DIR / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    total_size = sum(
        os.path.getsize(REPLAY_DIR / "ticks" / f"tick_{t:04d}.json")
        for t in range(TOTAL_TICKS + 1)
    )
    timeline_size = os.path.getsize(REPLAY_DIR / "timeline.json")
    print(f"  Replay chunks: {TOTAL_TICKS + 1} files, {total_size / 1024:.0f} KB total")
    print(f"  Timeline (single file): {timeline_size / 1024:.0f} KB")
    print(f"  Meta: {REPLAY_DIR / 'meta.json'}")

    return timeline, meta


# ============================================================
# 2.3 — SUMMARY STATISTICS (for charts and paper figures)
# ============================================================

def compute_statistics(snapshots: dict, messages: list, bus_events: list, chronicle: list):
    """Compute all summary statistics."""
    print("\nComputing statistics...")

    stats = {}

    # --- Wellbeing curves (Figure 3) ---
    print("  Wellbeing curves...")
    wellbeing = {}
    for aid in range(12):
        wellbeing[aid] = []
        for tick in range(TOTAL_TICKS + 1):
            agent = snapshots[tick]["agents"].get(str(aid), {})
            wellbeing[aid].append({
                "tick": tick,
                "wellbeing": round(agent.get("wellbeing", 0), 4),
            })
    avg_wellbeing = []
    for tick in range(TOTAL_TICKS + 1):
        vals = [wellbeing[aid][tick]["wellbeing"] for aid in range(12)]
        avg_wellbeing.append({
            "tick": tick,
            "mean": round(sum(vals) / len(vals), 4),
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
        })
    stats["wellbeing_curves"] = {
        "per_agent": wellbeing,
        "average": avg_wellbeing,
    }

    # --- Maslow level progression ---
    print("  Maslow progression...")
    maslow = {}
    for aid in range(12):
        maslow[aid] = []
        for tick in range(TOTAL_TICKS + 1):
            agent = snapshots[tick]["agents"].get(str(aid), {})
            maslow[aid].append({
                "tick": tick,
                "level": agent.get("maslow_level", 1),
            })
    avg_maslow = []
    for tick in range(TOTAL_TICKS + 1):
        vals = [maslow[aid][tick]["level"] for aid in range(12)]
        avg_maslow.append({
            "tick": tick,
            "mean": round(sum(vals) / len(vals), 2),
            "min": min(vals),
            "max": max(vals),
        })
    stats["maslow_progression"] = {
        "per_agent": maslow,
        "average": avg_maslow,
    }

    # --- Structure growth (Figure 4) ---
    print("  Structure growth...")
    structure_growth = []
    for tick in range(TOTAL_TICKS + 1):
        snap = snapshots[tick]
        count = 0
        new_this_tick = []
        for row in snap.get("tiles", []):
            for tile in row:
                for s in tile.get("structures", []):
                    count += 1
                    if s.get("built_tick") == tick:
                        new_this_tick.append({
                            "type": s["structure_type"],
                            "builder": s["builder_id"],
                            "name": s.get("custom_name", ""),
                        })
        structure_growth.append({
            "tick": tick,
            "total": count,
            "new": len(new_this_tick),
            "new_structures": new_this_tick,
        })
    stats["structure_growth"] = structure_growth

    # --- Communication volume (Figure 4) ---
    print("  Communication volume...")
    msgs_by_tick = defaultdict(list)
    for m in messages:
        msgs_by_tick[m["tick"]].append(m)

    comm_volume = []
    cumulative = 0
    for tick in range(TOTAL_TICKS + 1):
        tick_msgs = msgs_by_tick.get(tick, [])
        count = len(tick_msgs)
        cumulative += count
        pairs = set()
        for m in tick_msgs:
            pair = tuple(sorted([m["sender_id"], m["receiver_id"]]))
            pairs.add(pair)
        comm_volume.append({
            "tick": tick,
            "count": count,
            "cumulative": cumulative,
            "unique_pairs": len(pairs),
        })
    stats["communication_volume"] = comm_volume

    # --- Innovation timeline (Figure 6) ---
    print("  Innovation timeline...")
    # Get innovations from the final snapshot's discovered_recipes
    final_recipes = snapshots[TOTAL_TICKS].get("discovered_recipes", [])
    innovations = []
    for r in final_recipes:
        innovations.append({
            "name": r["output_name"],
            "description": r.get("output_description", ""),
            "discovered_by": r["discovered_by"],
            "discovered_tick": r["discovered_tick"],
            "times_built": r.get("times_built", 0),
            "effect_type": r.get("effect_type", ""),
            "inputs": r.get("inputs", []),
        })
    innovations.sort(key=lambda x: x["discovered_tick"])

    # Innovation rate by era
    era1_innovations = [i for i in innovations if i["discovered_tick"] <= 50]
    era2_innovations = [i for i in innovations if 50 < i["discovered_tick"] <= 60]
    era3_innovations = [i for i in innovations if i["discovered_tick"] > 60]

    stats["innovation_timeline"] = {
        "innovations": innovations,
        "by_era": {
            "era1_count": len(era1_innovations),
            "era1_rate": round(len(era1_innovations) / 50, 3) if era1_innovations else 0,
            "era2_count": len(era2_innovations),
            "era2_rate": round(len(era2_innovations) / 10, 3) if era2_innovations else 0,
            "era3_count": len(era3_innovations),
            "era3_rate": round(len(era3_innovations) / 10, 3) if era3_innovations else 0,
        },
        "acceleration_factor": (
            round((len(era2_innovations) / 10) / (len(era1_innovations) / 50), 1)
            if era1_innovations else None
        ),
    }

    # --- Specialisation progression (Figure 5) ---
    print("  Specialisation progression...")
    spec_events = [
        e for e in bus_events if e.get("type") == "specialisation_gained"
    ]
    spec_timeline = []
    for e in spec_events:
        spec_timeline.append({
            "tick": e.get("tick"),
            "agent": e.get("agent_id"),
            "skill": e.get("data", {}).get("skill", e.get("data", {}).get("specialisation", "")),
            "tier": e.get("data", {}).get("tier", ""),
        })
    spec_timeline.sort(key=lambda x: (x["tick"], x["agent"]))

    # Per-agent specialisation at each tick
    spec_by_agent = {}
    for aid in range(12):
        spec_by_agent[aid] = []
        for tick in range(TOTAL_TICKS + 1):
            agent = snapshots[tick]["agents"].get(str(aid), {})
            activity = agent.get("activity_counts", {})
            specs = agent.get("specialisations", [])
            spec_by_agent[aid].append({
                "tick": tick,
                "specialisations": specs,
                "spec_count": len(specs),
                "top_activity": max(activity, key=activity.get) if activity else None,
                "top_count": max(activity.values()) if activity else 0,
            })

    stats["specialisation_progression"] = {
        "events": spec_timeline,
        "per_agent": spec_by_agent,
    }

    # --- Need levels over time ---
    print("  Need levels...")
    need_curves = {"water": [], "food": [], "material": []}
    for tick in range(TOTAL_TICKS + 1):
        for need_type in ["water", "food", "material"]:
            vals = []
            for aid in range(12):
                agent = snapshots[tick]["agents"].get(str(aid), {})
                val = agent.get("needs", {}).get("levels", {}).get(need_type, 0)
                vals.append(val)
            need_curves[need_type].append({
                "tick": tick,
                "mean": round(sum(vals) / len(vals), 4),
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
            })
    stats["need_curves"] = need_curves

    # --- Relationship network ---
    print("  Relationship network...")
    relationship_snapshots = {}
    for tick in [0, 10, 20, 30, 40, 50, 60, 70]:
        snap = snapshots[tick]
        network = {}
        for aid_str, agent in snap["agents"].items():
            aid = int(aid_str)
            rels = agent.get("relationships", {})
            network[aid] = {}
            for partner_str, rel in rels.items():
                pid = int(partner_str)
                network[aid][pid] = {
                    "interactions": rel.get("interaction_count", 0),
                    "positive": rel.get("positive_count", 0),
                    "negative": rel.get("negative_count", 0),
                    "bonded": rel.get("is_bonded", False),
                    "last_tick": rel.get("last_interaction_tick", 0),
                }
        relationship_snapshots[tick] = network

    stats["relationship_network"] = relationship_snapshots

    # --- Agent profiles (final state) ---
    print("  Agent profiles...")
    agent_profiles = {}
    final_snap = snapshots[TOTAL_TICKS]
    for aid in range(12):
        agent = final_snap["agents"][str(aid)]
        rels = agent.get("relationships", {})
        bonds = [int(k) for k, v in rels.items() if v.get("is_bonded")]
        top_partner = max(
            rels.items(),
            key=lambda x: x[1].get("interaction_count", 0),
            default=(None, {})
        )

        # Find this agent's innovation
        innovation = None
        for r in final_recipes:
            if r["discovered_by"] == aid:
                innovation = r["output_name"]
                break

        agent_profiles[aid] = {
            "id": aid,
            "final_position": [agent["position"]["x"], agent["position"]["y"]],
            "final_wellbeing": round(agent["wellbeing"], 4),
            "final_maslow": agent.get("maslow_level", 1),
            "specialisations": agent.get("specialisations", []),
            "structures_built": agent.get("structures_built_count", 0),
            "innovation_proposed": innovation,
            "known_recipes": agent.get("known_recipes", []),
            "total_relationships": len(rels),
            "bonds": bonds,
            "top_partner": int(top_partner[0]) if top_partner[0] else None,
            "top_partner_interactions": top_partner[1].get("interaction_count", 0) if top_partner[0] else 0,
            "tiles_visited": len(agent.get("visited_tiles", [])),
            "activity_counts": {
                k: v for k, v in agent.get("activity_counts", {}).items() if v > 0
            },
            "memory_count": len(agent.get("memories", [])),
        }
    stats["agent_profiles"] = agent_profiles

    # --- Era comparison ---
    print("  Era comparison...")

    def era_stats(start, end):
        """Compute aggregate stats for a tick range."""
        start_snap = snapshots[start]
        end_snap = snapshots[end]

        # Count structures
        def count_structures(snap):
            c = 0
            for row in snap.get("tiles", []):
                for tile in row:
                    c += len(tile.get("structures", []))
            return c

        struct_start = count_structures(start_snap)
        struct_end = count_structures(end_snap)

        # Count recipes
        recipes_start = len(start_snap.get("discovered_recipes", []))
        recipes_end = len(end_snap.get("discovered_recipes", []))

        # Wellbeing
        wb_start = [
            start_snap["agents"][str(i)].get("wellbeing", 0) for i in range(12)
        ]
        wb_end = [
            end_snap["agents"][str(i)].get("wellbeing", 0) for i in range(12)
        ]

        # Maslow
        ml_start = [
            start_snap["agents"][str(i)].get("maslow_level", 1) for i in range(12)
        ]
        ml_end = [
            end_snap["agents"][str(i)].get("maslow_level", 1) for i in range(12)
        ]

        # Messages in range
        era_msgs = [
            m for m in messages if start <= m["tick"] <= end
        ]

        return {
            "ticks": f"{start}-{end}",
            "duration": end - start,
            "structures_start": struct_start,
            "structures_end": struct_end,
            "structures_delta": struct_end - struct_start,
            "recipes_start": recipes_start,
            "recipes_end": recipes_end,
            "recipes_delta": recipes_end - recipes_start,
            "wellbeing_start_mean": round(sum(wb_start) / len(wb_start), 4),
            "wellbeing_end_mean": round(sum(wb_end) / len(wb_end), 4),
            "maslow_start_mean": round(sum(ml_start) / len(ml_start), 2),
            "maslow_end_mean": round(sum(ml_end) / len(ml_end), 2),
            "messages": len(era_msgs),
        }

    stats["era_comparison"] = {
        "era1_survival_trap": era_stats(0, 50),
        "era2_emergence_explosion": era_stats(50, 60),
        "era3_sustained_flourishing": era_stats(60, 70),
        "full_simulation": era_stats(0, 70),
    }

    # --- Governance timeline ---
    print("  Governance timeline...")
    rule_events = [
        e for e in bus_events
        if e.get("type") in ("rule_proposed", "rule_accepted", "rule_established")
    ]
    rule_events.sort(key=lambda x: x.get("tick", 0))
    stats["governance_timeline"] = [
        {
            "type": e["type"],
            "tick": e.get("tick"),
            "agent": e.get("agent_id"),
            "data": e.get("data", {}),
        }
        for e in rule_events
    ]

    # --- Action distribution ---
    print("  Action distribution...")
    action_events = [e for e in bus_events if e.get("type") == "action_taken"]
    action_counts_by_era = {
        "era1": defaultdict(int),
        "era2": defaultdict(int),
        "era3": defaultdict(int),
    }
    for e in action_events:
        tick = e.get("tick", 0)
        action_type = e.get("data", {}).get("action_type", "unknown")
        if tick <= 50:
            action_counts_by_era["era1"][action_type] += 1
        elif tick <= 60:
            action_counts_by_era["era2"][action_type] += 1
        else:
            action_counts_by_era["era3"][action_type] += 1

    stats["action_distribution"] = {
        era: dict(sorted(counts.items(), key=lambda x: -x[1]))
        for era, counts in action_counts_by_era.items()
    }

    # --- Chronicle summary ---
    print("  Chronicle summary...")
    milestones = [
        e for e in chronicle if e.get("type") == "milestone"
    ]
    stats["milestones"] = [
        {
            "tick": m.get("tick"),
            "name": m.get("data", {}).get("name", ""),
            "commentary": m.get("data", {}).get("commentary", ""),
        }
        for m in milestones
    ]

    # --- Build events timeline ---
    print("  Build events...")
    build_events = [e for e in bus_events if e.get("type") == "structure_built"]
    build_events.sort(key=lambda x: x.get("tick", 0))
    stats["build_events"] = [
        {
            "tick": e.get("tick"),
            "agent": e.get("agent_id"),
            "type": e.get("data", {}).get("structure_type", ""),
            "position": e.get("data", {}).get("position"),
        }
        for e in build_events
    ]

    # Save all stats
    for name, data in stats.items():
        path = STATS_DIR / f"{name}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        size = os.path.getsize(path) / 1024
        print(f"  Saved {name}.json ({size:.1f} KB)")

    return stats


# ============================================================
# 2.4 — DATA MANIFEST
# ============================================================

def build_manifest(stats: dict, meta: dict):
    """Build a manifest of all exported data for the website."""
    print("\nBuilding data manifest...")

    manifest = {
        "generated": "2026-04-01",
        "simulation": {
            "total_ticks": TOTAL_TICKS,
            "agent_count": 12,
            "grid_size": [meta["grid_width"], meta["grid_height"]],
            "model": "claude-sonnet-4-20250514",
            "eras": meta["eras"],
            "upgrade_tick": 50,
        },
        "final_state": {
            "structures": stats["structure_growth"][-1]["total"],
            "recipes": stats["innovation_timeline"]["innovations"][-1]["name"] if stats["innovation_timeline"]["innovations"] else "none",
            "recipe_count": len(stats["innovation_timeline"]["innovations"]),
            "avg_wellbeing": stats["wellbeing_curves"]["average"][-1]["mean"],
            "messages_total": stats["communication_volume"][-1]["cumulative"],
        },
        "data_files": {
            "replay": {
                "timeline": str(REPLAY_DIR / "timeline.json"),
                "meta": str(REPLAY_DIR / "meta.json"),
                "tick_chunks": str(REPLAY_DIR / "ticks" / "tick_NNNN.json"),
                "tick_count": TOTAL_TICKS + 1,
            },
            "statistics": {},
            "interviews": {},
            "snapshots": {
                "directory": str(SNAP_DIR),
                "count": TOTAL_TICKS + 1,
            },
            "raw_events": {
                "chronicle": str(SIM_DIR / "chronicle.jsonl"),
                "bus_events": str(SIM_DIR / "bus_events.jsonl"),
                "messages": str(SIM_DIR / "messages.jsonl"),
                "events": str(SIM_DIR / "events.jsonl"),
            },
        },
        "website_requirements": {
            "fishbowl_replay": {
                "needed": ["replay/timeline.json", "replay/meta.json"],
                "status": "READY",
            },
            "simulations_page": {
                "needed": [
                    "stats/wellbeing_curves.json",
                    "stats/structure_growth.json",
                    "stats/communication_volume.json",
                    "stats/innovation_timeline.json",
                    "stats/era_comparison.json",
                    "stats/agent_profiles.json",
                ],
                "status": "READY",
            },
            "methodology_page": {
                "needed": ["stats/era_comparison.json", "stats/action_distribution.json"],
                "status": "READY",
            },
            "discovery_page": {
                "needed": [
                    "stats/innovation_timeline.json",
                    "stats/specialisation_progression.json",
                    "stats/governance_timeline.json",
                    "stats/milestones.json",
                ],
                "status": "READY",
            },
            "interview_transcripts": {
                "needed": ["interviews/tick_*/all_interviews.json"],
                "status": "READY" if (INTERVIEWS_DIR / "tick_0070").exists() else "MISSING",
            },
            "paper_figures": {
                "fig3_wellbeing": "stats/wellbeing_curves.json",
                "fig4_cumulative": ["stats/structure_growth.json", "stats/communication_volume.json", "stats/innovation_timeline.json"],
                "fig5_specialisation": "stats/specialisation_progression.json",
                "fig6_innovation": "stats/innovation_timeline.json",
                "status": "READY",
            },
        },
    }

    # List all stat files
    for f in sorted(STATS_DIR.glob("*.json")):
        manifest["data_files"]["statistics"][f.stem] = str(f)

    # List interview directories
    for d in sorted(INTERVIEWS_DIR.iterdir()):
        if d.is_dir() and d.name.startswith("tick_"):
            all_file = d / "all_interviews.json"
            manifest["data_files"]["interviews"][d.name] = {
                "directory": str(d),
                "all_interviews": str(all_file) if all_file.exists() else "MISSING",
                "entity_count": len(list(d.glob("entity_*.json"))),
            }

    # Verify all requirements
    all_ready = True
    for page, req in manifest["website_requirements"].items():
        if req.get("status") != "READY":
            all_ready = False
            print(f"  WARNING: {page} — status: {req.get('status')}")

    manifest["all_requirements_met"] = all_ready

    with open(EXPORT_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"  Manifest saved: {EXPORT_DIR / 'manifest.json'}")
    print(f"  All requirements met: {all_ready}")

    return manifest


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("AgentCiv Data Processing Pipeline")
    print("=" * 60)

    ensure_dirs()

    # Load source data
    snapshots = load_all_snapshots()
    messages = load_jsonl("messages.jsonl")
    bus_events = load_jsonl("bus_events.jsonl")
    chronicle = load_jsonl("chronicle.jsonl")

    print(f"\nSource data loaded:")
    print(f"  Snapshots: {len(snapshots)}")
    print(f"  Messages: {len(messages)}")
    print(f"  Bus events: {len(bus_events)}")
    print(f"  Chronicle entries: {len(chronicle)}")

    # Phase 2.1 + 2.2: Build replay data
    timeline, meta = build_replay_data(snapshots, messages, bus_events)

    # Phase 2.3: Compute statistics
    stats = compute_statistics(snapshots, messages, bus_events, chronicle)

    # Phase 2.4: Build manifest
    manifest = build_manifest(stats, meta)

    # Summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"\nExport directory: {EXPORT_DIR}")
    print(f"\nReplay data:")
    print(f"  {REPLAY_DIR / 'timeline.json'}")
    print(f"  {REPLAY_DIR / 'meta.json'}")
    print(f"  {REPLAY_DIR / 'ticks/'} ({TOTAL_TICKS + 1} chunk files)")
    print(f"\nStatistics ({len(list(STATS_DIR.glob('*.json')))} files):")
    for f in sorted(STATS_DIR.glob("*.json")):
        print(f"  {f.name}")
    print(f"\nManifest: {EXPORT_DIR / 'manifest.json'}")

    # Quick stats summary
    ec = stats["era_comparison"]
    print(f"\n--- Key Numbers ---")
    print(f"Final structures: {ec['full_simulation']['structures_end']}")
    print(f"Final recipes: {ec['full_simulation']['recipes_end']}")
    print(f"Final wellbeing: {ec['full_simulation']['wellbeing_end_mean']}")
    print(f"Total messages: {stats['communication_volume'][-1]['cumulative']}")

    it = stats["innovation_timeline"]
    print(f"Innovations: {len(it['innovations'])} total")
    print(f"  Era 1 (0-50): {it['by_era']['era1_count']} ({it['by_era']['era1_rate']}/tick)")
    print(f"  Era 2 (50-60): {it['by_era']['era2_count']} ({it['by_era']['era2_rate']}/tick)")
    print(f"  Era 3 (60-70): {it['by_era']['era3_count']} ({it['by_era']['era3_rate']}/tick)")
    if it["acceleration_factor"]:
        print(f"  Acceleration (Era 2 vs Era 1): {it['acceleration_factor']}×")


if __name__ == "__main__":
    main()
