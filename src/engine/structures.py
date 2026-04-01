"""Structure mechanics for Agent Civilisation.

Handles building, functional effects, storage operations, and decay.
Structures are persistent world modifications placed by agents — the mechanism
that enables civilisational emergence through compounding complexity.

Structure types (configurable):
  - Shelter: reduces degradation rate for agents on the tile
  - Storage: holds resources accessible to any agent
  - Marker: contains a persistent text message from the builder
  - Path: reduces movement cost on the tile
"""

from __future__ import annotations

import logging

from src.config import SimulationConfig
from src.types import (
    AgentState,
    Structure,
    StructureType,
    Tile,
)

logger = logging.getLogger("agent_civilisation.structures")


# ======================================================================
# Recipe / prerequisite checks
# ======================================================================

def get_recipe(structure_type: str, config: SimulationConfig) -> list[str] | None:
    """Get the resource recipe for a structure type. Returns None if unknown."""
    struct_config = config.structures.get(structure_type)
    if struct_config is None:
        return None
    return list(struct_config.get("requires", []))


def can_build(agent: AgentState, structure_type: str, config: SimulationConfig) -> bool:
    """Check if agent has the required resources in inventory to build."""
    recipe = get_recipe(structure_type, config)
    if recipe is None:
        return False
    inventory_copy = list(agent.inventory)
    for required in recipe:
        if required in inventory_copy:
            inventory_copy.remove(required)
        else:
            return False
    return True


# ======================================================================
# Building
# ======================================================================

def build_structure(
    agent: AgentState,
    structure_type: str,
    tile: Tile,
    config: SimulationConfig,
    tick: int,
    message: str | None = None,
) -> Structure | None:
    """Build a structure on the tile, consuming resources from agent inventory.

    Returns the Structure if built, None if requirements not met.
    """
    recipe = get_recipe(structure_type, config)
    if recipe is None:
        return None

    # Verify and consume resources from inventory
    inventory_copy = list(agent.inventory)
    for required in recipe:
        if required in inventory_copy:
            inventory_copy.remove(required)
        else:
            return None

    # Commit: consume resources
    agent.inventory = inventory_copy

    # Get structure config
    struct_config = config.structures.get(structure_type, {})
    capacity = float(struct_config.get("capacity", 0.0))

    # Create structure
    try:
        stype = StructureType(structure_type)
    except ValueError:
        # Custom structure type from config — treat as marker for now
        stype = StructureType.MARKER

    structure = Structure(
        structure_type=stype,
        builder_id=agent.id,
        built_tick=tick,
        health=1.0,
        message=message if stype == StructureType.MARKER else None,
        capacity=capacity,
    )

    tile.structures.append(structure)

    logger.info(
        "Agent %d built %s at (%d, %d) — %d structures now on tile",
        agent.id, structure_type, tile.position.x, tile.position.y,
        len(tile.structures),
    )

    return structure


# ======================================================================
# Functional effects
# ======================================================================

def get_shelter_degradation_multiplier(tile: Tile, config: SimulationConfig) -> float:
    """Return degradation rate multiplier for shelter effects on tile.

    STACKING: Multiple shelters compound with diminishing returns.
    First shelter gives full effect_strength, each additional gives 50% of previous.
    """
    struct_config = config.structures.get("shelter", {})
    base_effect = struct_config.get("effect_strength", 0.5)

    shelter_count = sum(
        1 for s in tile.structures
        if s.structure_type == StructureType.SHELTER and s.health > 0
    )
    if shelter_count == 0:
        return 1.0

    # Diminishing returns: each additional shelter adds 50% of the previous effect
    # 1 shelter: base_effect, 2: base_effect * 1.5, 3: base_effect * 1.75, etc.
    # Result is multiplied against the degradation rate, so lower = better
    total_reduction = 0.0
    contribution = 1.0 - base_effect  # how much the first shelter reduces (e.g. 0.5)
    for _ in range(shelter_count):
        total_reduction += contribution
        contribution *= 0.5  # each additional contributes half as much

    return max(0.1, 1.0 - total_reduction)  # floor at 0.1 (never zero degradation)


def get_path_cost_multiplier(tile: Tile, config: SimulationConfig) -> float:
    """Return movement cost multiplier for path effects on tile.

    STACKING: Multiple paths compound with diminishing returns.
    """
    struct_config = config.structures.get("path", {})
    base_effect = struct_config.get("effect_strength", 0.5)

    path_count = sum(
        1 for s in tile.structures
        if s.structure_type == StructureType.PATH and s.health > 0
    )
    if path_count == 0:
        return 1.0

    # Same diminishing returns as shelter
    total_reduction = 0.0
    contribution = 1.0 - base_effect
    for _ in range(path_count):
        total_reduction += contribution
        contribution *= 0.5

    return max(0.1, 1.0 - total_reduction)


# ======================================================================
# Innovation structure effects (custom mechanics applied by tick engine)
# ======================================================================

def get_custom_effect_strength(tile: Tile, effect_type: str) -> float:
    """Return the total strength of a custom innovation effect on this tile.

    Each matching healthy structure contributes 0.25 base, with diminishing
    returns for stacking (50% reduction per additional).
    """
    count = sum(
        1 for s in tile.structures
        if s.health > 0 and s.effect_type == effect_type
    )
    if count == 0:
        return 0.0

    base = 0.25
    total = 0.0
    contrib = base
    for _ in range(count):
        total += contrib
        contrib *= 0.5
    return total


def get_gathering_bonus(tile: Tile) -> float:
    """Return gathering multiplier from boost_gathering structures.

    Returns 1.0 (no bonus) if no matching structures.
    """
    strength = get_custom_effect_strength(tile, "boost_gathering")
    return 1.0 + strength  # e.g. 1.25 with one structure


def get_regen_bonus(tile: Tile) -> float:
    """Return regen multiplier from boost_regeneration structures.

    Returns 1.0 (no bonus) if no matching structures.
    """
    strength = get_custom_effect_strength(tile, "boost_regeneration")
    return 1.0 + strength * 2.0  # stronger effect: 1.5 with one structure


def get_need_depletion_reduction(tile: Tile) -> float:
    """Return need depletion reduction factor from reduce_need_depletion structures.

    Returns 1.0 (no reduction) if no matching structures.
    Lower values = slower depletion = better for agent.
    """
    strength = get_custom_effect_strength(tile, "reduce_need_depletion")
    return max(0.5, 1.0 - strength)  # floor at 50% reduction


def get_wellbeing_bonus(tile: Tile) -> float:
    """Return per-tick wellbeing bonus from boost_wellbeing structures."""
    strength = get_custom_effect_strength(tile, "boost_wellbeing")
    return strength * 0.08  # 0.02 per structure (0.25 * 0.08)


def get_perception_bonus(tile: Tile) -> float:
    """Return perception range bonus from extend_perception structures."""
    strength = get_custom_effect_strength(tile, "extend_perception")
    return min(2.0, strength * 4.0)  # up to +2 tiles, 1.0 per structure


# ======================================================================
# Settlement detection
# ======================================================================

def count_structures_nearby(
    position: "Position",
    radius: int,
    tiles: list[list["Tile"]],
    grid_width: int,
    grid_height: int,
) -> int:
    """Count healthy structures within Chebyshev distance of position."""
    from src.types import Position  # avoid circular at module level
    total = 0
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            nx, ny = position.x + dx, position.y + dy
            if 0 <= nx < grid_width and 0 <= ny < grid_height:
                for s in tiles[nx][ny].structures:
                    if s.health > 0:
                        total += 1
    return total


def is_in_settlement(
    position: "Position",
    tiles: list[list["Tile"]],
    config: SimulationConfig,
) -> bool:
    """Check if a position is within a settlement (enough structures nearby)."""
    return count_structures_nearby(
        position,
        config.settlement_range,
        tiles,
        config.grid_width,
        config.grid_height,
    ) >= config.settlement_structure_threshold


# ======================================================================
# Repair
# ======================================================================

def repair_structure(
    agent: AgentState,
    tile: Tile,
    config: SimulationConfig,
) -> "Structure | None":
    """Repair the most damaged structure on the tile, consuming 1 material.

    Returns the repaired Structure if successful, None if no material
    or no damaged structures.
    """
    if "material" not in agent.inventory:
        return None

    # Find the most damaged structure that isn't at full health
    damaged = [
        s for s in tile.structures
        if s.health > 0 and s.health < 1.0
    ]
    if not damaged:
        return None

    # Repair the most damaged one
    target = min(damaged, key=lambda s: s.health)
    agent.inventory.remove("material")
    target.health = min(1.0, target.health + config.repair_health_restore)

    logger.info(
        "Agent %d repaired %s at (%d, %d) — health now %.0f%%",
        agent.id,
        target.custom_name or target.structure_type.value,
        tile.position.x, tile.position.y,
        target.health * 100,
    )

    return target


# ======================================================================
# Storage operations
# ======================================================================

def store_resource(
    agent: AgentState,
    tile: Tile,
    resource_type: str,
) -> bool:
    """Deposit a resource from agent inventory into a storage structure on tile.

    Returns True if stored, False if no storage or resource not held.
    """
    if resource_type not in agent.inventory:
        return False

    for structure in tile.structures:
        if structure.structure_type == StructureType.STORAGE and structure.health > 0:
            total_stored = sum(structure.stored_resources.values())
            if total_stored < structure.capacity:
                agent.inventory.remove(resource_type)
                current = structure.stored_resources.get(resource_type, 0.0)
                structure.stored_resources[resource_type] = current + 1.0
                return True
    return False


def retrieve_from_storage(
    tile: Tile,
    resource_type: str,
) -> bool:
    """Take a resource from a storage structure on tile.

    Returns True if a unit was removed (caller adds to agent inventory).
    """
    for structure in tile.structures:
        if structure.structure_type == StructureType.STORAGE and structure.health > 0:
            if structure.stored_resources.get(resource_type, 0.0) >= 1.0:
                structure.stored_resources[resource_type] -= 1.0
                if structure.stored_resources[resource_type] <= 0:
                    del structure.stored_resources[resource_type]
                return True
    return False


def get_storage_contents(tile: Tile) -> dict[str, float]:
    """Return total contents across all storage structures on the tile."""
    contents: dict[str, float] = {}
    for structure in tile.structures:
        if structure.structure_type == StructureType.STORAGE and structure.health > 0:
            for rtype, amount in structure.stored_resources.items():
                contents[rtype] = contents.get(rtype, 0.0) + amount
    return contents


# ======================================================================
# Marker operations
# ======================================================================

def read_marker(tile: Tile) -> list[tuple[int, str]]:
    """Read all marker messages on the tile.

    Returns list of (builder_id, message) for each healthy marker.
    """
    results: list[tuple[int, str]] = []
    for structure in tile.structures:
        if (
            structure.structure_type == StructureType.MARKER
            and structure.health > 0
            and structure.message
        ):
            results.append((structure.builder_id, structure.message))
    return results


# ======================================================================
# Decay
# ======================================================================

def decay_structures(
    tiles: list[list[Tile]],
    config: SimulationConfig,
) -> list[tuple[int, int, Structure]]:
    """Apply decay to all structures across the grid.

    Returns list of (x, y, structure) for structures that decayed to nothing.
    """
    removed: list[tuple[int, int, Structure]] = []

    for x, col in enumerate(tiles):
        for y, tile in enumerate(col):
            if not tile.structures:
                continue

            surviving: list[Structure] = []
            for structure in tile.structures:
                stype = structure.structure_type.value
                struct_config = config.structures.get(stype, {})
                decay_rate = struct_config.get("decay_rate", 0.001)

                structure.health -= decay_rate
                if structure.health <= 0:
                    removed.append((x, y, structure))
                else:
                    surviving.append(structure)

            tile.structures = surviving

    return removed


# ======================================================================
# Utility
# ======================================================================

_EFFECT_DESCRIPTIONS: dict[str, str] = {
    "boost_gathering": "increases gathering yield nearby",
    "boost_regeneration": "resources regenerate faster on this tile",
    "reduce_need_depletion": "needs deplete slower for entities here",
    "boost_wellbeing": "boosts wellbeing for entities here",
    "extend_perception": "extends perception range for entities here",
}


def describe_structures(tile: Tile) -> list[str]:
    """Return human-readable descriptions of structures on a tile."""
    descriptions: list[str] = []
    for s in tile.structures:
        if s.health <= 0:
            continue
        # Use custom name if it's an innovation
        name = s.custom_name if s.custom_name else s.structure_type.value
        desc = f"{name} (health {s.health:.0%}, built by Entity {s.builder_id})"
        if s.structure_type == StructureType.MARKER and s.message:
            desc += f' — message: "{s.message}"'
        if s.structure_type == StructureType.STORAGE and s.stored_resources:
            contents = ", ".join(f"{v:.0f} {k}" for k, v in s.stored_resources.items())
            desc += f" — holds: {contents}"
        # Show innovation mechanical effects
        if s.effect_type and s.effect_type in _EFFECT_DESCRIPTIONS:
            desc += f" — EFFECT: {_EFFECT_DESCRIPTIONS[s.effect_type]}"
        elif s.custom_name and s.custom_description:
            desc += f" — {s.custom_description[:80]}"
        descriptions.append(desc)
    return descriptions
