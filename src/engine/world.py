"""World grid, tiles, and resource mechanics.

The World class holds the 2D grid of Tiles and provides methods for
resource distribution, depletion, regeneration, and spatial queries.
All parameters come from SimulationConfig — nothing is hardcoded.
"""

from __future__ import annotations

import random
from typing import Optional

from src.config import SimulationConfig
from src.types import (
    AgentState,
    Position,
    Resource,
    Structure,
    TerrainType,
    Tile,
)


class World:
    """The simulation world: a 2D grid of tiles with resources and terrain."""

    def __init__(
        self,
        width: int,
        height: int,
        tiles: list[list[Tile]],
    ) -> None:
        self.width = width
        self.height = height
        self.tiles = tiles  # tiles[x][y]

    # ------------------------------------------------------------------
    # Spatial queries
    # ------------------------------------------------------------------

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Return the tile at (x, y), or None if out of bounds."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[x][y]
        return None

    def get_resources_at(self, position: Position) -> dict[str, Resource]:
        """Return all resources on the tile at *position* that have amount > 0."""
        tile = self.get_tile(position.x, position.y)
        if tile is None:
            return {}
        return {
            rtype: res
            for rtype, res in tile.resources.items()
            if res.amount > 0
        }

    def deplete_resource(
        self,
        position: Position,
        resource_type: str,
        rate: float,
    ) -> float:
        """Reduce resource at *position* by *rate*.

        Returns the actual amount depleted (may be less than *rate* if
        the resource was nearly exhausted).
        """
        tile = self.get_tile(position.x, position.y)
        if tile is None:
            return 0.0
        res = tile.resources.get(resource_type)
        if res is None or res.amount <= 0:
            return 0.0
        actual = min(rate, res.amount)
        res.amount = max(0.0, res.amount - actual)
        return actual

    def regenerate_all(self, config: SimulationConfig) -> None:
        """Regenerate every resource on every tile toward its max_amount."""
        for x in range(self.width):
            for y in range(self.height):
                tile = self.tiles[x][y]
                for res in tile.resources.values():
                    if res.amount < res.max_amount:
                        res.amount = min(
                            res.max_amount,
                            res.amount + config.resource_regeneration_rate,
                        )

    def get_agents_near(
        self,
        position: Position,
        radius: float,
        agents: dict[int, AgentState],
        exclude_id: Optional[int] = None,
    ) -> list[AgentState]:
        """Return all agents within Chebyshev *radius* of *position*.

        Optionally exclude one agent (typically the querying agent itself).
        """
        result: list[AgentState] = []
        for agent in agents.values():
            if exclude_id is not None and agent.id == exclude_id:
                continue
            if position.distance_to(agent.position) <= radius:
                result.append(agent)
        return result

    def get_structures_at(self, position: Position) -> list[Structure]:
        """Return all structures on the tile at *position* with health > 0."""
        tile = self.get_tile(position.x, position.y)
        if tile is None:
            return []
        return [s for s in tile.structures if s.health > 0]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height


# ======================================================================
# World generation helpers
# ======================================================================

def _generate_terrain(
    width: int,
    height: int,
    config: SimulationConfig,
    rng: random.Random,
) -> list[list[TerrainType]]:
    """Generate a terrain map.

    Mostly plain, with random rocky and dense patches so that
    movement cost varies across the world.
    """
    terrain: list[list[TerrainType]] = [
        [TerrainType.PLAIN for _ in range(height)]
        for _ in range(width)
    ]

    # Scatter some rocky patches
    num_patches = max(1, (width * height) // 80)
    for _ in range(num_patches):
        cx, cy = rng.randint(0, width - 1), rng.randint(0, height - 1)
        radius = rng.randint(2, 4)
        patch_type = rng.choice([TerrainType.ROCKY, TerrainType.DENSE])
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < width and 0 <= ny < height:
                    # Probability falls off with distance from centre
                    dist = max(abs(dx), abs(dy))
                    if rng.random() < 1.0 - (dist / (radius + 1)):
                        terrain[nx][ny] = patch_type

    return terrain


def _distribute_resources_clustered(
    tiles: list[list[Tile]],
    config: SimulationConfig,
    rng: random.Random,
) -> None:
    """Place resources in clusters — each type gets distinct zones.

    This is the KEY distribution mode: water clusters in one area,
    food in another, material elsewhere. No tile gets all resource types,
    which forces agents to move and creates trade/coordination conditions.
    """
    width, height = len(tiles), len(tiles[0])

    for rtype in config.resource_types:
        for _ in range(config.resource_cluster_count):
            # Pick a random cluster centre
            cx = rng.randint(0, width - 1)
            cy = rng.randint(0, height - 1)
            radius = config.resource_cluster_radius

            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        dist = max(abs(dx), abs(dy))
                        # Amount falls off from centre
                        falloff = 1.0 - (dist / (radius + 1))
                        amount = config.resource_max_per_tile * falloff
                        if amount > 0:
                            tiles[nx][ny].resources[rtype] = Resource(
                                resource_type=rtype,
                                amount=amount,
                                max_amount=config.resource_max_per_tile,
                                regeneration_rate=config.resource_regeneration_rate,
                            )


def _distribute_resources_scattered(
    tiles: list[list[Tile]],
    config: SimulationConfig,
    rng: random.Random,
) -> None:
    """Place resources randomly across the grid.

    Each tile has a small chance of containing each resource type.
    """
    width, height = len(tiles), len(tiles[0])
    # Roughly 15% of tiles get each resource type
    probability = 0.15

    for rtype in config.resource_types:
        for x in range(width):
            for y in range(height):
                if rng.random() < probability:
                    amount = rng.uniform(0.2, config.resource_max_per_tile)
                    tiles[x][y].resources[rtype] = Resource(
                        resource_type=rtype,
                        amount=amount,
                        max_amount=config.resource_max_per_tile,
                        regeneration_rate=config.resource_regeneration_rate,
                    )


def _distribute_resources_banded(
    tiles: list[list[Tile]],
    config: SimulationConfig,
    rng: random.Random,
) -> None:
    """Place resources in horizontal bands — one band per resource type.

    Creates distinct zones that agents must traverse.
    """
    width, height = len(tiles), len(tiles[0])
    n_types = len(config.resource_types)
    band_height = max(1, height // n_types)

    for i, rtype in enumerate(config.resource_types):
        y_start = i * band_height
        y_end = min(height, (i + 1) * band_height) if i < n_types - 1 else height

        for x in range(width):
            for y in range(y_start, y_end):
                # Some variation within the band
                amount = rng.uniform(0.3, config.resource_max_per_tile)
                tiles[x][y].resources[rtype] = Resource(
                    resource_type=rtype,
                    amount=amount,
                    max_amount=config.resource_max_per_tile,
                    regeneration_rate=config.resource_regeneration_rate,
                )


def _distribute_resources_random(
    tiles: list[list[Tile]],
    config: SimulationConfig,
    rng: random.Random,
) -> None:
    """Fully random placement — every tile gets a random resource type at random amount."""
    width, height = len(tiles), len(tiles[0])
    for x in range(width):
        for y in range(height):
            # 1-2 random resource types per tile
            n = rng.randint(0, 2)
            chosen = rng.sample(config.resource_types, min(n, len(config.resource_types)))
            for rtype in chosen:
                amount = rng.uniform(0.1, config.resource_max_per_tile)
                tiles[x][y].resources[rtype] = Resource(
                    resource_type=rtype,
                    amount=amount,
                    max_amount=config.resource_max_per_tile,
                    regeneration_rate=config.resource_regeneration_rate,
                )


def generate_tiles(config: SimulationConfig, rng: random.Random | None = None) -> World:
    """Create the World with terrain and resources from config.

    This is the primary factory function. Environment.generate_world()
    wraps this to build the full WorldState.
    """
    if rng is None:
        rng = random.Random()

    width, height = config.grid_width, config.grid_height

    # Step 1: Terrain
    terrain = _generate_terrain(width, height, config, rng)

    # Step 2: Build empty tiles
    tiles: list[list[Tile]] = [
        [
            Tile(position=Position(x, y), terrain=terrain[x][y])
            for y in range(height)
        ]
        for x in range(width)
    ]

    # Step 3: Distribute resources
    distributors = {
        "clustered": _distribute_resources_clustered,
        "scattered": _distribute_resources_scattered,
        "banded": _distribute_resources_banded,
        "random": _distribute_resources_random,
    }
    distributor = distributors.get(config.resource_distribution, _distribute_resources_clustered)
    distributor(tiles, config, rng)

    return World(width=width, height=height, tiles=tiles)
