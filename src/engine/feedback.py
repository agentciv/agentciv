"""Feedback loop mechanics for Agent Civilisation.

Implements the three core feedback loops that create the "solutions create
problems" dynamic essential for open-ended evolution:

1. **Crowding**: Multiple agents gathering from the same tile depletes
   resources faster. Settlements must manage population density.

2. **Maintenance**: Structures consume resources each tick. Complexity
   has an upkeep cost — civilisations can collapse if maintenance
   outstrips production.

3. **Gathering Pressure / Environmental Co-evolution**: Heavy gathering
   degrades a resource's regeneration rate. The world pushes back
   against exploitation, forcing agents to rotate gathering sites or
   innovate (e.g. build paths to reach farther resources).

These three loops ensure that early solutions (clustering near resources,
building many structures, over-gathering) create new problems that drive
the next wave of innovation.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.config import SimulationConfig
from src.types import (
    AgentState,
    Position,
    Resource,
    Structure,
    StructureType,
    Tile,
)

logger = logging.getLogger("agent_civilisation.feedback")


# ======================================================================
# 1. Crowding — more agents on a tile = faster resource depletion
# ======================================================================

def crowding_depletion_rate(
    base_rate: float,
    agents_on_tile: int,
    config: SimulationConfig,
) -> float:
    """Return the effective depletion rate adjusted for crowding.

    When multiple agents gather from the same tile, each agent depletes
    at a higher rate. The multiplier scales linearly with agent count:
        effective = base * (1 + (n - 1) * (multiplier - 1))
    So with 1 agent the rate is unchanged; with 2 agents at multiplier
    1.5, each agent depletes at 1.5x; with 3 at 2.0x, etc.

    Args:
        base_rate: The normal resource depletion rate per gather.
        agents_on_tile: Number of agents currently on the same tile.
        config: Simulation config (for crowding_depletion_multiplier).

    Returns:
        Adjusted depletion rate. Always >= base_rate.
    """
    if agents_on_tile <= 1:
        return base_rate
    mult = config.crowding_depletion_multiplier
    # Linear scale: each additional agent adds (mult - 1) * base_rate
    factor = 1.0 + (agents_on_tile - 1) * (mult - 1.0)
    return base_rate * factor


def count_agents_on_tile(
    position: Position,
    agents: dict[int, AgentState],
    exclude_id: Optional[int] = None,
) -> int:
    """Count how many agents are on the exact tile at *position*."""
    count = 0
    for agent in agents.values():
        if exclude_id is not None and agent.id == exclude_id:
            continue
        if agent.position.x == position.x and agent.position.y == position.y:
            count += 1
    return count


# ======================================================================
# 2. Maintenance — structures consume resources to survive
# ======================================================================

def apply_maintenance(
    tiles: list[list[Tile]],
    config: SimulationConfig,
) -> list[tuple[int, int, Structure, str]]:
    """Apply per-tick maintenance cost to all structures.

    Each structure tries to consume `structure_maintenance_cost` from the
    tile's natural resources each tick. If the tile can't supply enough,
    the structure takes extra health damage proportional to the shortfall.

    Returns:
        List of (x, y, structure, resource_type) for each successful
        maintenance consumption (for bus event emission).
    """
    maintenance_cost = config.structure_maintenance_cost
    if maintenance_cost <= 0:
        return []

    consumed: list[tuple[int, int, Structure, str]] = []

    for x, col in enumerate(tiles):
        for y, tile in enumerate(col):
            if not tile.structures:
                continue

            for structure in tile.structures:
                if structure.health <= 0:
                    continue

                # Try to consume from tile resources
                fed = False
                for rtype, resource in tile.resources.items():
                    if resource.amount >= maintenance_cost:
                        resource.amount -= maintenance_cost
                        consumed.append((x, y, structure, rtype))
                        fed = True
                        break

                if not fed:
                    # No resources available — structure takes extra decay
                    # Penalty is proportional to maintenance cost (2x normal decay)
                    structure.health -= maintenance_cost * 2
                    if structure.health < 0:
                        structure.health = 0

    return consumed


# ======================================================================
# 3. Gathering Pressure / Environmental Co-evolution
# ======================================================================

def record_gathering_pressure(
    tile: Tile,
    resource_type: str,
    amount_gathered: float,
) -> None:
    """Record gathering activity on a resource, increasing its pressure.

    Gathering pressure accumulates and decays slowly, tracking how
    heavily a resource is being exploited. High pressure reduces
    the effective regeneration rate.
    """
    resource = tile.resources.get(resource_type)
    if resource is not None:
        resource.gathering_pressure += amount_gathered


def decay_gathering_pressure(tiles: list[list[Tile]], decay_rate: float = 0.02) -> None:
    """Naturally decay gathering pressure across all tiles each tick.

    Pressure decays toward zero so resources can recover when
    exploitation stops.
    """
    for col in tiles:
        for tile in col:
            for resource in tile.resources.values():
                if resource.gathering_pressure > 0:
                    resource.gathering_pressure = max(
                        0.0,
                        resource.gathering_pressure - decay_rate,
                    )


def effective_regeneration_rate(
    resource: Resource,
    tile: Tile,
    config: SimulationConfig,
) -> float:
    """Return the actual regeneration rate after accounting for gathering pressure
    AND positive structure feedback.

    Negative: gathering_pressure reduces regeneration.
    Positive: structures on the tile BOOST regeneration (cultivated land effect).

    This dual system means built-up areas can overcome gathering pressure,
    creating a genuine positive feedback loop for civilisation.
    """
    base_rate = resource.regeneration_rate

    # Positive feedback: structures boost regen
    structure_bonus = getattr(config, "structure_regen_bonus", 0.15)
    active_structures = sum(1 for s in tile.structures if s.health > 0)
    # Also check for boost_regeneration innovation structures (extra bonus)
    regen_innovation_bonus = 0.0
    for s in tile.structures:
        if s.health > 0 and getattr(s, "effect_type", None) == "boost_regeneration":
            regen_innovation_bonus += 0.5  # strong bonus from innovation structures

    positive_multiplier = 1.0 + (active_structures * structure_bonus) + regen_innovation_bonus

    if not config.enable_environmental_coevolution:
        return base_rate * positive_multiplier

    # Negative feedback: gathering pressure
    pressure = resource.gathering_pressure
    if pressure <= 0:
        return base_rate * positive_multiplier

    penalty_floor = config.heavy_gathering_regen_penalty
    factor = max(penalty_floor, 1.0 - pressure)

    return base_rate * factor * positive_multiplier
