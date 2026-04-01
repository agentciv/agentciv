#!/usr/bin/env python3
"""Export recorded simulation data into chunked format for the frontend replay engine.

Usage:
    python3 scripts/export_replay.py                          # defaults
    python3 scripts/export_replay.py --input data/simulation_state --output replay_data
    python3 scripts/export_replay.py --chunk-size 50          # ticks per chunk

Input: raw simulation recordings (snapshots/, events.jsonl, chronicle.jsonl, messages.jsonl)
Output: chunked JSON files ready for the frontend to lazy-load.

Output structure:
    replay_data/
      metadata.json           # simulation info + chunk index
      snapshots/
        chunk_000_049.json    # world states for ticks 0-49
        chunk_050_099.json    # etc.
      events/
        chunk_000_049.json    # events for ticks 0-49
        chunk_050_099.json    # etc.
      chronicle.json          # all chronicle entries
      messages.json           # all messages
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.engine.persistence import SimulationEncoder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export simulation data for frontend replay")
    parser.add_argument(
        "--input", "-i",
        default="data/simulation_state",
        help="Input directory containing snapshots/, events.jsonl, etc.",
    )
    parser.add_argument(
        "--output", "-o",
        default="src/frontend/public/replay_data",
        help="Output directory for chunked replay data",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50,
        help="Number of ticks per chunk (default: 50)",
    )
    parser.add_argument(
        "--name",
        default="Civilisation Alpha",
        help="Name for this simulation run",
    )
    return parser.parse_args()


def load_snapshots(input_dir: Path) -> dict[int, dict]:
    """Load all per-tick snapshot files, keyed by tick number."""
    snapshots_dir = input_dir / "snapshots"
    if not snapshots_dir.exists():
        print(f"ERROR: No snapshots directory found at {snapshots_dir}")
        print("Did you run the simulation with --record flag?")
        sys.exit(1)

    snapshots: dict[int, dict] = {}
    for f in sorted(snapshots_dir.glob("tick_*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
            tick = data.get("tick", -1)
            snapshots[tick] = data
        except (json.JSONDecodeError, KeyError) as e:
            print(f"WARNING: Skipping corrupt snapshot {f}: {e}")

    return snapshots


def load_jsonl(filepath: Path) -> list[dict]:
    """Load a JSONL file (one JSON object per line)."""
    if not filepath.exists():
        return []
    entries: list[dict] = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def chunk_by_tick(items: list[dict], chunk_size: int, max_tick: int) -> dict[str, list[dict]]:
    """Group items by tick into chunks. Returns {chunk_name: [items]}."""
    chunks: dict[str, list[dict]] = {}
    for start in range(0, max_tick + 1, chunk_size):
        end = min(start + chunk_size - 1, max_tick)
        chunk_name = f"chunk_{start:03d}_{end:03d}"
        chunk_items = [item for item in items if start <= item.get("tick", -1) <= end]
        if chunk_items:
            chunks[chunk_name] = chunk_items
    return chunks


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    chunk_size = args.chunk_size

    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Chunk size: {chunk_size} ticks")
    print()

    # ---- Load raw data ----
    print("Loading snapshots...")
    snapshots = load_snapshots(input_dir)
    if not snapshots:
        print("ERROR: No snapshots found. Nothing to export.")
        sys.exit(1)

    ticks = sorted(snapshots.keys())
    min_tick = ticks[0]
    max_tick = ticks[-1]
    print(f"  Found {len(snapshots)} snapshots (tick {min_tick} to {max_tick})")

    # Get config and agent info from the last snapshot
    last_snapshot = snapshots[max_tick]
    agent_count = len(last_snapshot.get("agents", {}))
    grid_width = last_snapshot.get("grid_width", 0)
    grid_height = last_snapshot.get("grid_height", 0)

    # Determine log directory — may be same as input_dir or a sibling "logs" dir
    # Check input_dir first, then common alternatives
    def find_log_file(name: str) -> Path:
        """Search for a log file in input_dir, then data/logs, then parent/logs."""
        candidates = [
            input_dir / name,
            input_dir.parent / "logs" / name,
            Path("data/logs") / name,
        ]
        for c in candidates:
            if c.exists():
                return c
        return input_dir / name  # default (will return empty list via load_jsonl)

    print("Loading events...")
    # Prefer bus_events.jsonl (rich bus events with reasoning, observations, etc.)
    # Fall back to events.jsonl (basic agent-level triggers) if bus events not available
    bus_events_path = find_log_file("bus_events.jsonl")
    if bus_events_path.exists():
        events = load_jsonl(bus_events_path)
        print(f"  Found {len(events)} bus events (rich data) from {bus_events_path}")
    else:
        events_path = find_log_file("events.jsonl")
        events = load_jsonl(events_path)
        print(f"  Found {len(events)} events (basic) from {events_path}")
        if events:
            print("  TIP: Re-run simulation to generate bus_events.jsonl for richer replay data")

    print("Loading chronicle...")
    chronicle_path = find_log_file("chronicle.jsonl")
    chronicle = load_jsonl(chronicle_path)
    print(f"  Found {len(chronicle)} chronicle entries from {chronicle_path}")

    print("Loading messages...")
    messages_path = find_log_file("messages.jsonl")
    messages = load_jsonl(messages_path)
    print(f"  Found {len(messages)} messages")
    print()

    # ---- Create output directories ----
    (output_dir / "snapshots").mkdir(parents=True, exist_ok=True)
    (output_dir / "events").mkdir(parents=True, exist_ok=True)

    # ---- Chunk and write snapshots ----
    print("Writing snapshot chunks...")
    snapshot_chunks: list[dict] = []
    for start in range(min_tick, max_tick + 1, chunk_size):
        end = min(start + chunk_size - 1, max_tick)
        chunk_name = f"chunk_{start:03d}_{end:03d}"

        # Collect snapshots in this range
        chunk_data: dict[str, dict] = {}
        for tick in range(start, end + 1):
            if tick in snapshots:
                chunk_data[str(tick)] = snapshots[tick]

        if chunk_data:
            chunk_path = output_dir / "snapshots" / f"{chunk_name}.json"
            with open(chunk_path, "w") as f:
                json.dump(chunk_data, f, separators=(",", ":"))
            size_kb = chunk_path.stat().st_size / 1024
            print(f"  {chunk_name}: {len(chunk_data)} snapshots ({size_kb:.0f} KB)")
            snapshot_chunks.append({
                "name": chunk_name,
                "start_tick": start,
                "end_tick": end,
                "snapshot_count": len(chunk_data),
                "file": f"snapshots/{chunk_name}.json",
            })

    # ---- Chunk and write events ----
    print("Writing event chunks...")
    event_chunks: list[dict] = []
    for start in range(min_tick, max_tick + 1, chunk_size):
        end = min(start + chunk_size - 1, max_tick)
        chunk_name = f"chunk_{start:03d}_{end:03d}"

        chunk_events = [e for e in events if start <= e.get("tick", -1) <= end]
        if chunk_events:
            chunk_path = output_dir / "events" / f"{chunk_name}.json"
            with open(chunk_path, "w") as f:
                json.dump(chunk_events, f, separators=(",", ":"))
            size_kb = chunk_path.stat().st_size / 1024
            print(f"  {chunk_name}: {len(chunk_events)} events ({size_kb:.0f} KB)")
            event_chunks.append({
                "name": chunk_name,
                "start_tick": start,
                "end_tick": end,
                "event_count": len(chunk_events),
                "file": f"events/{chunk_name}.json",
            })

    # ---- Write chronicle and messages ----
    print("Writing chronicle...")
    with open(output_dir / "chronicle.json", "w") as f:
        json.dump(chronicle, f, separators=(",", ":"))

    print("Writing messages...")
    with open(output_dir / "messages.json", "w") as f:
        json.dump(messages, f, separators=(",", ":"))

    # ---- Write metadata ----
    print("Writing metadata...")
    metadata = {
        "name": args.name,
        "min_tick": min_tick,
        "max_tick": max_tick,
        "total_ticks": max_tick - min_tick + 1,
        "agent_count": agent_count,
        "grid_width": grid_width,
        "grid_height": grid_height,
        "total_events": len(events),
        "total_messages": len(messages),
        "total_chronicle_entries": len(chronicle),
        "chunk_size": chunk_size,
        "snapshot_chunks": snapshot_chunks,
        "event_chunks": event_chunks,
    }

    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # ---- Summary ----
    total_size = sum(
        f.stat().st_size for f in output_dir.rglob("*.json")
    )
    print()
    print(f"Export complete!")
    print(f"  Ticks: {min_tick} to {max_tick} ({max_tick - min_tick + 1} total)")
    print(f"  Agents: {agent_count}")
    print(f"  Events: {len(events)}")
    print(f"  Messages: {len(messages)}")
    print(f"  Chronicle: {len(chronicle)} entries")
    print(f"  Total size: {total_size / 1024 / 1024:.1f} MB")
    print(f"  Output: {output_dir}/")


if __name__ == "__main__":
    main()
