"""World generation and environmental shifts.

Provides:
- generate_world(): builds the initial WorldState from config
- apply_shift(): redistributes resources to force adaptation
"""

from __future__ import annotations

import random
from typing import Optional

from src.config import SimulationConfig
from src.types import (
    AgentState,
    Capabilities,
    NeedsState,
    Position,
    Resource,
    Tile,
    WorldState,
    CURIOSITY_INITIAL,
    WELLBEING_INITIAL,
)
from src.engine.world import World, generate_tiles


# ======================================================================
# World generation
# ======================================================================

def generate_world(config: SimulationConfig, seed: Optional[int] = None) -> tuple[World, WorldState]:
    """Create the initial World and WorldState from config.

    Returns (world, world_state) — the World object for spatial queries
    and the WorldState snapshot for persistence/tick loop.
    """
    rng = random.Random(seed)

    # Build the grid
    world = generate_tiles(config, rng)

    # Create initial agents
    agents: dict[int, AgentState] = {}
    for i in range(config.initial_agent_count):
        pos = _pick_spawn_position(
            config.new_agent_spawn,
            config.grid_width,
            config.grid_height,
            rng,
        )
        agent = _create_agent(
            agent_id=i,
            position=pos,
            config=config,
            born_tick=0,
        )
        agents[i] = agent

    world_state = WorldState(
        tick=0,
        grid_width=config.grid_width,
        grid_height=config.grid_height,
        tiles=world.tiles,
        agents=agents,
        next_agent_id=config.initial_agent_count,
    )

    return world, world_state


def create_new_agent(
    world_state: WorldState,
    config: SimulationConfig,
    rng: random.Random | None = None,
) -> AgentState:
    """Create a new agent and add it to world_state.

    Returns the newly created AgentState.
    """
    if rng is None:
        rng = random.Random()

    pos = _pick_spawn_position(
        config.new_agent_spawn,
        config.grid_width,
        config.grid_height,
        rng,
    )
    agent = _create_agent(
        agent_id=world_state.next_agent_id,
        position=pos,
        config=config,
        born_tick=world_state.tick,
    )
    world_state.agents[agent.id] = agent
    world_state.next_agent_id += 1
    return agent


# ======================================================================
# Environmental shifts
# ======================================================================

def apply_shift(world: World, config: SimulationConfig, rng: random.Random | None = None) -> None:
    """Apply an environmental shift to the world.

    Severity levels:
      - "mild": slightly shift cluster centres, add/remove small amounts
      - "moderate": significant redistribution, some zones swap
      - "severe": major upheaval — resources largely reshuffled
    """
    if rng is None:
        rng = random.Random()

    severity = config.shift_severity

    if severity == "mild":
        _shift_mild(world, config, rng)
    elif severity == "moderate":
        _shift_moderate(world, config, rng)
    elif severity == "severe":
        _shift_severe(world, config, rng)
    else:
        # Default to mild if unknown severity
        _shift_mild(world, config, rng)


def _shift_mild(world: World, config: SimulationConfig, rng: random.Random) -> None:
    """Mild shift: slightly redistribute resources.

    - Reduce some existing resource amounts by 10-30%
    - Add small new pockets near existing clusters
    """
    for x in range(world.width):
        for y in range(world.height):
            tile = world.tiles[x][y]
            for res in tile.resources.values():
                # 20% chance to lose some amount
                if rng.random() < 0.20:
                    res.amount *= rng.uniform(0.7, 0.9)
                    res.amount = max(0.0, res.amount)

    # Add a few small new pockets
    for rtype in config.resource_types:
        num_pockets = rng.randint(1, 2)
        for _ in range(num_pockets):
            cx = rng.randint(0, world.width - 1)
            cy = rng.randint(0, world.height - 1)
            radius = rng.randint(1, 3)
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    nx, ny = cx + dx, cy + dy
                    if world.in_bounds(nx, ny):
                        dist = max(abs(dx), abs(dy))
                        if rng.random() < 0.5 - (dist / (radius + 1)) * 0.3:
                            amount = config.resource_max_per_tile * rng.uniform(0.1, 0.4)
                            world.tiles[nx][ny].resources[rtype] = Resource(
                                resource_type=rtype,
                                amount=amount,
                                max_amount=config.resource_max_per_tile,
                                regeneration_rate=config.resource_regeneration_rate,
                            )


def _shift_moderate(world: World, config: SimulationConfig, rng: random.Random) -> None:
    """Moderate shift: more significant redistribution.

    - Deplete 30-60% of existing resources
    - Create new clusters in different locations
    """
    # Deplete existing resources
    for x in range(world.width):
        for y in range(world.height):
            tile = world.tiles[x][y]
            for res in tile.resources.values():
                if rng.random() < 0.50:
                    res.amount *= rng.uniform(0.4, 0.7)
                    res.amount = max(0.0, res.amount)

    # Create new clusters (fewer than initial, in new positions)
    for rtype in config.resource_types:
        num_clusters = max(1, config.resource_cluster_count // 2)
        for _ in range(num_clusters):
            cx = rng.randint(0, world.width - 1)
            cy = rng.randint(0, world.height - 1)
            radius = config.resource_cluster_radius
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    nx, ny = cx + dx, cy + dy
                    if world.in_bounds(nx, ny):
                        dist = max(abs(dx), abs(dy))
                        falloff = 1.0 - (dist / (radius + 1))
                        amount = config.resource_max_per_tile * falloff * rng.uniform(0.5, 1.0)
                        if amount > 0:
                            world.tiles[nx][ny].resources[rtype] = Resource(
                                resource_type=rtype,
                                amount=amount,
                                max_amount=config.resource_max_per_tile,
                                regeneration_rate=config.resource_regeneration_rate,
                            )


def _shift_severe(world: World, config: SimulationConfig, rng: random.Random) -> None:
    """Severe shift: major upheaval — resources largely reshuffled.

    - Wipe most existing resources (keep 10-20%)
    - Generate entirely new resource clusters
    """
    # Wipe most resources
    for x in range(world.width):
        for y in range(world.height):
            tile = world.tiles[x][y]
            rtypes_to_remove: list[str] = []
            for rtype, res in tile.resources.items():
                if rng.random() < 0.80:
                    rtypes_to_remove.append(rtype)
                else:
                    res.amount *= rng.uniform(0.1, 0.3)
            for rtype in rtypes_to_remove:
                del tile.resources[rtype]

    # Generate fresh clusters in new positions
    for rtype in config.resource_types:
        for _ in range(config.resource_cluster_count):
            cx = rng.randint(0, world.width - 1)
            cy = rng.randint(0, world.height - 1)
            radius = config.resource_cluster_radius
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    nx, ny = cx + dx, cy + dy
                    if world.in_bounds(nx, ny):
                        dist = max(abs(dx), abs(dy))
                        falloff = 1.0 - (dist / (radius + 1))
                        amount = config.resource_max_per_tile * falloff
                        if amount > 0:
                            world.tiles[nx][ny].resources[rtype] = Resource(
                                resource_type=rtype,
                                amount=amount,
                                max_amount=config.resource_max_per_tile,
                                regeneration_rate=config.resource_regeneration_rate,
                            )


# ======================================================================
# Internal helpers
# ======================================================================

def _pick_spawn_position(
    mode: str,
    width: int,
    height: int,
    rng: random.Random,
) -> Position:
    """Choose a spawn position for a new agent."""
    if mode == "edge":
        side = rng.choice(["top", "bottom", "left", "right"])
        if side == "top":
            return Position(rng.randint(0, width - 1), 0)
        elif side == "bottom":
            return Position(rng.randint(0, width - 1), height - 1)
        elif side == "left":
            return Position(0, rng.randint(0, height - 1))
        else:
            return Position(width - 1, rng.randint(0, height - 1))
    elif mode == "centre":
        cx, cy = width // 2, height // 2
        # Small random offset from centre
        return Position(
            cx + rng.randint(-3, 3),
            cy + rng.randint(-3, 3),
        )
    else:  # "random" or fallback
        return Position(
            rng.randint(0, width - 1),
            rng.randint(0, height - 1),
        )


def _create_agent(
    agent_id: int,
    position: Position,
    config: SimulationConfig,
    born_tick: int,
) -> AgentState:
    """Create a fresh AgentState with full needs, initial wellbeing, and healthy capabilities."""
    return AgentState(
        id=agent_id,
        position=position,
        needs=NeedsState.create_full(config.resource_types),
        wellbeing=WELLBEING_INITIAL,
        curiosity=CURIOSITY_INITIAL,
        capabilities=Capabilities.create_healthy(
            perception_range=float(config.agent_perception_range),
            movement_speed=config.agent_base_movement_speed,
            memory_capacity=config.agent_memory_capacity,
        ),
        memories=[],
        age=0,
        alive_since_tick=born_tick,
        inventory=[],
        activity_counts={},
        specialisations=[],
        known_recipes=[],
    )
