"""Agent-proposed innovation for Agent Civilisation.

Allows agents to propose entirely new structure types that don't exist
in the configuration. The LLM evaluates whether the proposed innovation
is feasible given the world's mechanics, and if approved, creates a new
dynamic structure type that can be built.

CRITICAL DESIGN: The innovation evaluation prompt is DISTINCT from the
composition evaluation prompt. Innovation asks "is this ENTIRELY NEW
thing feasible and what would it do?" — it expands the possibility space
beyond what currently exists. Composition asks "what does combining
existing things produce?" — it works within the known space.

This is the unbounded possibility space: agents can imagine and propose
structures that the simulation designers never conceived. The experiment
reveals what agents independently invent when given the freedom to create.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from src.config import SimulationConfig
from src.types import (
    AgentState,
    DiscoveredRecipe,
    Structure,
    StructureType,
    WorldState,
)
from src.engine.world import World

logger = logging.getLogger("agent_civilisation.innovation")


async def evaluate_innovation(
    agent: AgentState,
    description: str,
    world: World,
    world_state: WorldState,
    config: SimulationConfig,
    llm_client: Any,  # LLMClient — avoid circular import
) -> Optional[tuple[str, str, list[str], str]]:
    """Evaluate an agent's proposed innovation.

    Args:
        agent: The agent proposing the innovation.
        description: Free-text description of what they want to create.
        world: The world grid.
        world_state: Current world state.
        config: Simulation config.
        llm_client: LLM client for evaluation.

    Returns:
        (name, effect_description, recipe, effect_type) if approved, None if rejected.
        recipe is a list of resource types needed to build.
        effect_type maps to a base structure mechanic (shelter/storage/marker/path).
    """
    # Check that this isn't already a known structure type or recipe
    desc_lower = description.lower()
    for stype in ["shelter", "storage", "marker", "path"]:
        if stype in desc_lower:
            logger.debug(
                "Agent %d innovation rejected: '%s' matches existing type '%s'",
                agent.id, description, stype,
            )
            return None

    for recipe in world_state.discovered_recipes:
        if recipe.output_name.lower() in desc_lower:
            logger.debug(
                "Agent %d innovation rejected: '%s' matches existing recipe '%s'",
                agent.id, description, recipe.output_name,
            )
            return None

    # Build context about what already exists
    existing_types = ["shelter (reduces degradation)", "storage (holds resources)",
                      "marker (persistent message)", "path (reduces movement cost)"]

    existing_recipes_desc = ""
    if world_state.discovered_recipes:
        recipe_lines = [f"- {r.output_name}: {r.output_description}" for r in world_state.discovered_recipes[:10]]
        existing_recipes_desc = f"\n\nPreviously discovered structures:\n{chr(10).join(recipe_lines)}"

    # Agent's context
    agent_context = f"The proposing entity has {len(agent.inventory)} resources in inventory."
    if agent.specialisations:
        agent_context += f" They specialise in: {', '.join(agent.specialisations)}."

    prompt = f"""You are evaluating a proposed INNOVATION in a world simulation where entities gather resources, build structures, and form settlements.

An entity proposes to create: "{description}"

Existing structure types:
{chr(10).join(f'- {t}' for t in existing_types)}{existing_recipes_desc}

Available resource types in this world: {', '.join(config.resource_types)}

{agent_context}

Question: Is this innovation feasible and does it add something functionally NEW to the world? If yes, name it, describe its effect, and specify what resources are needed to build it.

Rules:
- The innovation must be DIFFERENT from existing structures and recipes
- It must be buildable from the world's available resources ({', '.join(config.resource_types)})
- It should serve a purpose in a resource-gathering survival world
- Cost should be proportional to benefit (powerful structures need more resources)
- If the proposal is too vague, too powerful, or redundant, reject it
- Be creative but balanced

Respond in EXACTLY this format (no other text):
NAME: [concise name]
EFFECT: [one sentence describing the functional effect]
EFFECT_TYPE: [choose the ONE best mechanical effect from this list:
  - reduce_degradation: reduces capability degradation when needs are low (like shelter)
  - store_resources: holds resources for later retrieval (like storage)
  - persistent_message: leaves a readable message or knowledge record (like marker)
  - reduce_movement_cost: makes the tile easier to cross (like path)
  - boost_gathering: agents on this tile gather more resources per action
  - boost_regeneration: resources on this tile regenerate faster
  - reduce_need_depletion: agents on this tile have slower need drain (food/water lasts longer)
  - boost_wellbeing: agents on this tile gain passive wellbeing (social/spiritual benefit)
  - extend_perception: agents on this tile can see further]
RECIPE: [comma-separated resource types needed, e.g. "material, material, food"]

Or if the innovation should be rejected:
REJECTED: [brief reason]"""

    # Use innovation evaluation model if specified, otherwise main model
    response = await llm_client.call_llm(prompt)
    return _parse_innovation_response(response, config)


_VALID_EFFECT_TYPES = {
    # Base 4 (map to existing structure types)
    "reduce_degradation", "store_resources", "persistent_message", "reduce_movement_cost",
    # Expanded civilisation effects (custom mechanics applied by tick engine)
    "boost_gathering",          # agents on tile gather more per action
    "boost_regeneration",       # resources on tile regenerate faster
    "reduce_need_depletion",    # agents on tile have slower need drain
    "boost_wellbeing",          # passive wellbeing bonus for agents on tile
    "extend_perception",        # agents on tile can see further
}

# Base effect types that map directly to existing StructureType mechanics
_EFFECT_TYPE_TO_STRUCTURE = {
    "reduce_degradation": StructureType.SHELTER,
    "store_resources": StructureType.STORAGE,
    "persistent_message": StructureType.MARKER,
    "reduce_movement_cost": StructureType.PATH,
}

# Custom effect types get MARKER as their base StructureType but their real
# effect is applied by the tick engine via the structure's effect_type field.
_CUSTOM_EFFECT_TYPES = {
    "boost_gathering", "boost_regeneration", "reduce_need_depletion",
    "boost_wellbeing", "extend_perception",
}


def _parse_innovation_response(
    response: str,
    config: SimulationConfig,
) -> Optional[tuple[str, str, list[str], str]]:
    """Parse the LLM's innovation evaluation response.

    Returns (name, effect, recipe, effect_type) if approved, None if rejected.
    """
    text = response.strip()

    if "REJECTED" in text.upper():
        return None

    name_match = re.search(r'NAME:\s*(.+)', text, re.IGNORECASE)
    effect_match = re.search(r'EFFECT:\s*(.+)', text, re.IGNORECASE)
    effect_type_match = re.search(r'EFFECT_TYPE:\s*(.+)', text, re.IGNORECASE)
    recipe_match = re.search(r'RECIPE:\s*(.+)', text, re.IGNORECASE)

    if name_match and effect_match and recipe_match:
        name = name_match.group(1).strip().rstrip(".")
        effect = effect_match.group(1).strip().rstrip(".")
        recipe_raw = recipe_match.group(1).strip()

        # Parse effect type — default to marker if missing or invalid
        effect_type = "marker"
        if effect_type_match:
            raw_et = effect_type_match.group(1).strip().lower()
            if raw_et in _VALID_EFFECT_TYPES:
                effect_type = raw_et

        # Parse recipe: comma-separated resource types
        recipe = [r.strip().lower() for r in recipe_raw.split(",") if r.strip()]

        # Validate: all recipe items must be valid resource types
        valid_resources = set(config.resource_types)
        for item in recipe:
            if item not in valid_resources:
                logger.debug(
                    "Innovation rejected: recipe item '%s' not a valid resource",
                    item,
                )
                return None

        if not recipe:
            return None

        if name and effect:
            return name, effect, recipe, effect_type

    return None


def register_innovation(
    agent: AgentState,
    name: str,
    effect: str,
    recipe: list[str],
    world_state: WorldState,
    effect_type: str = "marker",
) -> DiscoveredRecipe:
    """Register an approved innovation as a discoverable recipe.

    This makes the innovation buildable by any agent who knows the recipe.
    """
    dr = DiscoveredRecipe(
        inputs=sorted(recipe),  # sorted for consistent lookup
        output_name=name,
        output_description=effect,
        discovered_by=agent.id,
        discovered_tick=world_state.tick,
        effect_type=effect_type,
    )
    world_state.discovered_recipes.append(dr)

    # Broadcast: all agents can now build this innovation
    for a in world_state.agents.values():
        if name not in a.known_recipes:
            a.known_recipes.append(name)

    logger.info(
        "Agent %d innovation registered: %s (requires %s)",
        agent.id, name, recipe,
    )

    return dr


def build_innovation(
    agent: AgentState,
    recipe: DiscoveredRecipe,
    tile: Any,  # Tile
    world_state: WorldState,
) -> Optional[Structure]:
    """Build an innovation structure from an agent's inventory.

    Returns the Structure if built, None if agent lacks resources.
    """
    # Check inventory
    inventory_copy = list(agent.inventory)
    for resource in recipe.inputs:
        if resource in inventory_copy:
            inventory_copy.remove(resource)
        else:
            return None

    # Commit
    agent.inventory = inventory_copy
    recipe.times_built += 1

    # Map innovation's effect_type to a real StructureType for base mechanics.
    # Custom effect types (boost_gathering, etc.) get MARKER as base but their
    # real effect is applied by the tick engine via the effect_type field.
    struct_type = _EFFECT_TYPE_TO_STRUCTURE.get(recipe.effect_type, StructureType.MARKER)

    structure = Structure(
        structure_type=struct_type,
        builder_id=agent.id,
        built_tick=world_state.tick,
        health=1.0,
        custom_name=recipe.output_name,
        custom_description=recipe.output_description,
        # Store the innovation's effect type for custom mechanics
        effect_type=recipe.effect_type if recipe.effect_type in _CUSTOM_EFFECT_TYPES else None,
    )
    tile.structures.append(structure)

    logger.info(
        "Agent %d built innovation %s at (%d, %d)",
        agent.id, recipe.output_name, tile.position.x, tile.position.y,
    )

    return structure
