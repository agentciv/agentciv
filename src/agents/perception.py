"""Perception module for Agent Civilisation.

Determines what an agent can see (tiles, resources, other agents) and
detects events by comparing the current perception to the previous tick.

Also provides observe_after_action() for the agentic loop's mid-turn
observe step — lets the agent see the result of each action it takes.
"""

from __future__ import annotations

from src.config import SimulationConfig
from src.types import (
    Action,
    ActionType,
    AgentState,
    Capabilities,
    Event,
    EventType,
    Position,
    Resource,
    Tile,
)


# ---------------------------------------------------------------------------
# Visibility queries
# ---------------------------------------------------------------------------

def visible_tiles(
    position: Position,
    perception_range: float,
    grid: list[list[Tile]],
) -> list[Tile]:
    """Return all tiles within Chebyshev distance of *perception_range*.

    Uses the agent's CURRENT (possibly degraded) perception range, not the
    base value — degraded agents see less.
    """
    pr = int(perception_range)
    width = len(grid)
    height = len(grid[0]) if width > 0 else 0

    x_min = max(0, position.x - pr)
    x_max = min(width - 1, position.x + pr)
    y_min = max(0, position.y - pr)
    y_max = min(height - 1, position.y + pr)

    tiles: list[Tile] = []
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            tiles.append(grid[x][y])
    return tiles


def visible_resources(
    position: Position,
    perception_range: float,
    grid: list[list[Tile]],
) -> list[tuple[Position, Resource]]:
    """Return resources on visible tiles that have amount > 0."""
    results: list[tuple[Position, Resource]] = []
    for tile in visible_tiles(position, perception_range, grid):
        for resource in tile.resources.values():
            if resource.amount > 0:
                results.append((tile.position, resource))
    return results


def visible_agents(
    agent: AgentState,
    all_agents: dict[int, AgentState],
) -> list[AgentState]:
    """Return other agents within the agent's current perception range."""
    pr = agent.capabilities.perception_range
    result: list[AgentState] = []
    for other in all_agents.values():
        if other.id == agent.id:
            continue
        if agent.position.distance_to(other.position) <= pr:
            result.append(other)
    return result


# ---------------------------------------------------------------------------
# Event detection
# ---------------------------------------------------------------------------

def detect_events(
    agent: AgentState,
    previous_agents_in_perception: set[int],
    vis_agents: list[AgentState],
    vis_resources: list[tuple[Position, Resource]],
    config: SimulationConfig,
    tick: int,
) -> list[Event]:
    """Compare the current perception to previous state and emit events.

    Events returned:
    - AGENT_ENTERED_PERCEPTION: new agent visible that wasn't before
    - AGENT_LEFT_PERCEPTION: previously visible agent no longer visible
    - RESOURCE_DEPLETED: a position in agent.known_resources now has no resource
    - RESOURCE_DISCOVERED: new resource found not in known_resources
    - NEEDS_CRITICAL: any need just dropped below DEGRADATION_THRESHOLD
    - REFLECTION: periodic self-assessment trigger
    - PLAN_STEP_DUE: agent has pending plan steps ready to execute
    """
    events: list[Event] = []

    # --- Agent enter / leave perception ---
    current_visible_ids = {a.id for a in vis_agents}

    for aid in current_visible_ids - previous_agents_in_perception:
        events.append(Event(
            type=EventType.AGENT_ENTERED_PERCEPTION,
            tick=tick,
            agent_id=agent.id,
            data={"other_agent_id": aid},
        ))

    for aid in previous_agents_in_perception - current_visible_ids:
        events.append(Event(
            type=EventType.AGENT_LEFT_PERCEPTION,
            tick=tick,
            agent_id=agent.id,
            data={"other_agent_id": aid},
        ))

    # --- Resource discovery / depletion ---
    # Build a lookup of currently visible resource positions -> type
    visible_resource_positions: dict[tuple[int, int], str] = {}
    for pos, res in vis_resources:
        visible_resource_positions[(pos.x, pos.y)] = res.resource_type

    # Discovered: visible resources not already known
    for pos_tuple, rtype in visible_resource_positions.items():
        if pos_tuple not in agent.known_resources:
            events.append(Event(
                type=EventType.RESOURCE_DISCOVERED,
                tick=tick,
                agent_id=agent.id,
                data={"position": pos_tuple, "resource_type": rtype},
            ))

    # Depleted: known resources that are no longer visible with amount > 0
    # (only check positions within current perception range)
    pr = int(agent.capabilities.perception_range)
    for pos_tuple, rtype in list(agent.known_resources.items()):
        px, py = pos_tuple
        # Only check depletion for positions within perception range
        if max(abs(px - agent.position.x), abs(py - agent.position.y)) <= pr:
            if pos_tuple not in visible_resource_positions:
                events.append(Event(
                    type=EventType.RESOURCE_DEPLETED,
                    tick=tick,
                    agent_id=agent.id,
                    data={"position": pos_tuple, "resource_type": rtype},
                ))

    # --- Needs critical ---
    threshold = Capabilities.DEGRADATION_THRESHOLD
    for need_type, level in agent.needs.levels.items():
        if level < threshold:
            events.append(Event(
                type=EventType.NEEDS_CRITICAL,
                tick=tick,
                agent_id=agent.id,
                data={"need_type": need_type, "level": round(level, 3)},
            ))

    # --- Periodic reflection ---
    if agent.age > 0 and agent.age % config.agent_reflection_interval == 0:
        events.append(Event(
            type=EventType.REFLECTION,
            tick=tick,
            agent_id=agent.id,
            data={"age": agent.age},
        ))

    # --- Plan step due ---
    if agent.plan:
        events.append(Event(
            type=EventType.PLAN_STEP_DUE,
            tick=tick,
            agent_id=agent.id,
            data={"next_step": agent.plan[0], "remaining": len(agent.plan)},
        ))

    return events


# ---------------------------------------------------------------------------
# Mid-turn observation (for the agentic loop)
# ---------------------------------------------------------------------------

def observe_after_action(
    agent: AgentState,
    action: Action,
    grid: list[list[Tile]],
    all_agents: dict[int, AgentState],
    config: SimulationConfig,
) -> str:
    """Build a text observation after an action is executed.

    Called by the agentic loop after each action to let the agent
    see what happened. Returns a human-readable description.

    Examples:
    - "You moved south. You can now see 3 water resources and Agent 12."
    - "You gathered food. Your food need is now 0.8."
    - "You communicated with Agent 5."
    - "You set a new goal: find water."
    - "You updated your plan with 3 steps."
    - "You waited. Nothing changed."
    """
    parts: list[str] = []

    # Describe the action result
    if action.type == ActionType.MOVE:
        direction_name = _direction_name(action.direction)
        parts.append(f"You moved {direction_name}. You are now at [{agent.position.x}, {agent.position.y}].")

    elif action.type == ActionType.GATHER:
        rtype = action.resource_type or "unknown"
        parts.append(f"You gathered {rtype} into your inventory. Carrying: {', '.join(agent.inventory)} ({len(agent.inventory)} items).")

    elif action.type == ActionType.CONSUME:
        rtype = action.resource_type or "unknown"
        need_level = agent.needs.levels.get(rtype, 0.0)
        parts.append(f"You consumed {rtype}. Your {rtype} need is now {need_level:.2f}.")

    elif action.type == ActionType.BUILD:
        stype = action.structure_type or "unknown"
        parts.append(f"You built a {stype} at [{agent.position.x}, {agent.position.y}].")

    elif action.type == ActionType.STORE:
        rtype = action.resource_type or "unknown"
        parts.append(f"You stored {rtype} in a storage structure.")

    elif action.type == ActionType.READ_MARKER:
        parts.append("You read a marker.")

    elif action.type == ActionType.COMMUNICATE:
        target = action.target_agent_id
        if target is not None and target != -1:
            parts.append(f"You communicated with Agent {target}.")
        else:
            parts.append("You broadcast a message to nearby entities.")

    elif action.type == ActionType.SET_GOAL:
        parts.append(f"You set a new goal: {action.goal or 'unknown'}.")

    elif action.type == ActionType.UPDATE_PLAN:
        step_count = len(action.plan_steps) if action.plan_steps else 0
        parts.append(f"You updated your plan with {step_count} steps.")

    elif action.type == ActionType.WAIT:
        parts.append("You waited.")

    elif action.type == ActionType.COMPOSE:
        targets = action.compose_targets or []
        parts.append(f"You attempted to compose {' + '.join(targets)}.")

    elif action.type == ActionType.PROPOSE_INNOVATION:
        desc = action.innovation_description or "unknown"
        parts.append(f"You proposed an innovation: {desc}.")

    elif action.type == ActionType.PROPOSE_RULE:
        text = action.rule_text or "unknown"
        parts.append(f"You proposed a rule: \"{text}\".")

    elif action.type == ActionType.ACCEPT_RULE:
        parts.append(f"You accepted rule #{action.rule_id}.")

    elif action.type == ActionType.IGNORE_RULE:
        parts.append(f"You ignored rule #{action.rule_id}.")

    elif action.type == ActionType.DONE:
        parts.append("You ended your turn.")

    # Describe what the agent can now perceive
    vis_agents_list = visible_agents(agent, all_agents)
    vis_res_list = visible_resources(
        agent.position,
        agent.capabilities.perception_range,
        grid,
    )

    if vis_agents_list:
        agent_ids = [str(a.id) for a in vis_agents_list[:5]]
        agent_str = ", ".join(agent_ids)
        if len(vis_agents_list) > 5:
            agent_str += f" and {len(vis_agents_list) - 5} more"
        parts.append(f"You can see: Agent {agent_str}.")

    if vis_res_list:
        # Summarize by resource type
        resource_counts: dict[str, int] = {}
        for _pos, res in vis_res_list:
            resource_counts[res.resource_type] = resource_counts.get(res.resource_type, 0) + 1
        res_parts = [f"{count} {rtype}" for rtype, count in resource_counts.items()]
        parts.append(f"Visible resources: {', '.join(res_parts)}.")

    # Report need levels if any are concerning
    critical_needs = [
        (ntype, level) for ntype, level in agent.needs.levels.items()
        if level < Capabilities.DEGRADATION_THRESHOLD
    ]
    if critical_needs:
        need_strs = [f"{ntype}: {level:.2f}" for ntype, level in critical_needs]
        parts.append(f"Warning - critical needs: {', '.join(need_strs)}.")

    if not parts:
        parts.append("Nothing notable happened.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _direction_name(direction: tuple[int, int] | None) -> str:
    """Convert a (dx, dy) tuple to a direction name."""
    if direction is None:
        return "nowhere"
    names = {
        (0, -1): "north", (0, 1): "south", (1, 0): "east", (-1, 0): "west",
        (1, -1): "northeast", (-1, -1): "northwest",
        (1, 1): "southeast", (-1, 1): "southwest",
        (0, 0): "nowhere",
    }
    return names.get(direction, f"direction ({direction[0]},{direction[1]})")
