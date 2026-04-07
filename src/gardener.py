"""Gardener Mode — mid-run intervention for AI civilisations.

The Gardener can observe the simulation and make interventions between ticks:
- Broadcast messages to all agents
- Modify resource levels on specific tiles or globally
- Trigger environmental events (drought, abundance, etc.)
- Adjust agent needs (feed/starve specific agents)
- Introduce new agents mid-run
- Pause and inspect the world state

Available via:
- CLI: agentciv-sim run --gardener (interactive terminal prompts between ticks)
- MCP: agentciv_sim_intervene() tool (Claude Code can be the gardener)
"""

from __future__ import annotations

import sys
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    pass  # WorldState import for type checking only


# ── Intervention Actions ────────────────────────────────────────────────────

class GardenerAction:
    """Represents a single gardener intervention."""

    def __init__(self, action_type: str, params: dict[str, Any] | None = None):
        self.action_type = action_type
        self.params = params or {}

    def __repr__(self) -> str:
        return f"GardenerAction({self.action_type}, {self.params})"


def apply_action(world_state: Any, action: GardenerAction) -> str:
    """Apply a gardener action to the world state. Returns description of what happened."""

    if action.action_type == "broadcast":
        msg = action.params.get("message", "")
        count = 0
        for agent in world_state.agents:
            if hasattr(agent, "memory") and agent.memory is not None:
                agent.memory.add({
                    "type": "broadcast",
                    "source": "gardener",
                    "content": msg,
                    "tick": world_state.tick,
                })
                count += 1
        return f"Broadcast to {count} agents: {msg}"

    elif action.action_type == "resource_boost":
        amount = action.params.get("amount", 0.3)
        x = action.params.get("x")
        y = action.params.get("y")

        if x is not None and y is not None:
            # Specific tile
            tile = world_state.tiles.get((x, y))
            if tile:
                for rtype in tile.resources:
                    tile.resources[rtype] = min(1.0, tile.resources[rtype] + amount)
                return f"Boosted resources at ({x},{y}) by {amount}"
            return f"No tile at ({x},{y})"
        else:
            # Global boost
            count = 0
            for tile in world_state.tiles.values():
                for rtype in tile.resources:
                    tile.resources[rtype] = min(1.0, tile.resources[rtype] + amount)
                count += 1
            return f"Boosted resources on {count} tiles by {amount}"

    elif action.action_type == "resource_drain":
        amount = action.params.get("amount", 0.3)
        count = 0
        for tile in world_state.tiles.values():
            for rtype in tile.resources:
                tile.resources[rtype] = max(0.0, tile.resources[rtype] - amount)
            count += 1
        return f"Drained resources on {count} tiles by {amount}"

    elif action.action_type == "feed_agent":
        agent_id = action.params.get("agent_id")
        amount = action.params.get("amount", 0.5)
        for agent in world_state.agents:
            if str(getattr(agent, "id", None)) == str(agent_id):
                if hasattr(agent, "needs"):
                    for need in agent.needs:
                        agent.needs[need] = min(1.0, agent.needs.get(need, 0) + amount)
                return f"Fed agent {agent_id} (needs +{amount})"
        return f"Agent {agent_id} not found"

    elif action.action_type == "event":
        event_type = action.params.get("event_type", "drought")
        severity = action.params.get("severity", 0.5)

        if event_type == "drought":
            for tile in world_state.tiles.values():
                if "water" in tile.resources:
                    tile.resources["water"] *= (1.0 - severity)
            return f"Drought event (severity {severity}): water reduced globally"

        elif event_type == "abundance":
            for tile in world_state.tiles.values():
                for rtype in tile.resources:
                    tile.resources[rtype] = min(1.0, tile.resources[rtype] + severity * 0.5)
            return f"Abundance event (severity {severity}): all resources boosted"

        elif event_type == "migration":
            # Could spawn new agents — depends on world_state API
            return f"Migration event triggered (severity {severity})"

        return f"Unknown event type: {event_type}"

    elif action.action_type == "inspect":
        # Return world state summary
        alive = sum(1 for a in world_state.agents if getattr(a, "alive", True))
        total = len(world_state.agents)
        return (
            f"Tick {world_state.tick} | "
            f"Agents: {alive}/{total} alive | "
            f"Tiles: {len(world_state.tiles)}"
        )

    elif action.action_type == "pause":
        return "Simulation paused (gardener inspection)"

    elif action.action_type == "skip":
        return ""  # No action, continue

    else:
        return f"Unknown action: {action.action_type}"


# ── CLI Gardener ────────────────────────────────────────────────────────────

class CLIGardener:
    """Interactive terminal gardener — prompts between ticks."""

    def __init__(self, interval: int = 10):
        self.interval = interval  # Prompt every N ticks
        self.history: list[str] = []

    def should_prompt(self, tick: int) -> bool:
        """Check if we should prompt the gardener this tick."""
        return tick > 0 and tick % self.interval == 0

    def prompt(self, world_state: Any) -> GardenerAction | None:
        """Interactive prompt between ticks. Returns action or None to skip."""
        alive = sum(1 for a in world_state.agents if getattr(a, "alive", True))
        total = len(world_state.agents)

        print()
        print(f"  ── Gardener Mode ── Tick {world_state.tick} ──")
        print(f"  Agents: {alive}/{total} alive")
        print()
        print("  Actions:")
        print("    [enter]     Continue (no intervention)")
        print("    b <msg>     Broadcast message to all agents")
        print("    boost       Boost all resources (+0.3)")
        print("    drain       Drain all resources (-0.3)")
        print("    drought     Trigger drought event")
        print("    abundance   Trigger abundance event")
        print("    inspect     Show world state summary")
        print("    q           Stop simulation")
        print()

        try:
            raw = input("  Gardener> ").strip()
        except (EOFError, KeyboardInterrupt):
            return GardenerAction("skip")

        if not raw:
            return GardenerAction("skip")

        if raw.lower() == "q":
            return GardenerAction("stop")

        if raw.lower().startswith("b "):
            msg = raw[2:].strip()
            return GardenerAction("broadcast", {"message": msg})

        if raw.lower() == "boost":
            return GardenerAction("resource_boost", {"amount": 0.3})

        if raw.lower() == "drain":
            return GardenerAction("resource_drain", {"amount": 0.3})

        if raw.lower() == "drought":
            return GardenerAction("event", {"event_type": "drought", "severity": 0.5})

        if raw.lower() == "abundance":
            return GardenerAction("event", {"event_type": "abundance", "severity": 0.5})

        if raw.lower() == "inspect":
            return GardenerAction("inspect")

        print(f"    Unknown command: {raw}")
        return GardenerAction("skip")

    def post_tick(self, world_state: Any, tick: int) -> bool:
        """Called after each tick. Returns False to stop the simulation."""
        if not self.should_prompt(tick):
            return True

        action = self.prompt(world_state)
        if action is None or action.action_type == "skip":
            return True

        if action.action_type == "stop":
            print("  Gardener stopped the simulation.")
            return False

        result = apply_action(world_state, action)
        if result:
            print(f"  → {result}")
            self.history.append(f"[tick {tick}] {result}")

        return True
