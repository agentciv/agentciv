"""Composition engine for Agent Civilisation.

Allows agents to combine existing structures on a tile into higher-tier
structures. When an agent composes two structures, the engine:

1. Checks if a known recipe exists for that combination
2. If yes: builds the output structure, removes the inputs, records it
3. If no: calls the LLM to evaluate whether this combination produces
   something meaningful (the COMPOSITION evaluation prompt)
4. If the LLM approves: creates a new DiscoveredRecipe, builds the output,
   removes the inputs

CRITICAL DESIGN: The composition evaluation prompt is DISTINCT from the
innovation evaluation prompt. Composition asks "what does combining these
EXISTING things produce?" — it works within the known possibility space.
Innovation asks "is this ENTIRELY NEW thing feasible?" — it expands the
possibility space. Different cognitive tasks for the LLM.

This is the adjacent possible in action: new possibilities emerge from
combinations of existing structures, exactly as Kauffman described.
"""

from __future__ import annotations

import logging
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

logger = logging.getLogger("agent_civilisation.composition")


async def attempt_composition(
    agent: AgentState,
    targets: list[str],
    world: World,
    world_state: WorldState,
    config: SimulationConfig,
    llm_client: Any,  # LLMClient — avoid circular import
) -> Optional[tuple[str, str]]:
    """Attempt to compose structures on the agent's current tile.

    Args:
        agent: The agent performing the composition.
        targets: Sorted list of structure type names to combine.
        world: The world grid.
        world_state: Current world state.
        config: Simulation config.
        llm_client: LLM client for evaluating unknown combinations.

    Returns:
        (output_name, description) if successful, None if failed.
    """
    tile = world.get_tile(agent.position.x, agent.position.y)
    if tile is None:
        return None

    # Verify the structures exist on this tile
    found_structures: list[Structure] = []
    remaining_targets = list(targets)

    for structure in tile.structures:
        if structure.health <= 0:
            continue
        stype_val = structure.structure_type.value
        if stype_val in remaining_targets:
            found_structures.append(structure)
            remaining_targets.remove(stype_val)

    if remaining_targets:
        # Not all required structures are on this tile
        logger.debug(
            "Agent %d composition failed: missing structures %s on tile (%d, %d)",
            agent.id, remaining_targets, agent.position.x, agent.position.y,
        )
        return None

    # Sort targets for consistent lookup
    sorted_targets = sorted(targets)

    # Check if this recipe is already known
    known_recipe = _find_recipe(sorted_targets, world_state)
    if known_recipe is not None:
        # Known recipe — build it directly
        return _apply_recipe(
            agent, known_recipe, found_structures, tile, world_state,
        )

    # Unknown combination — ask the LLM to evaluate
    result = await _evaluate_composition(
        agent, sorted_targets, found_structures, config, llm_client,
    )

    if result is None:
        return None

    output_name, output_description, effect_type = result

    # Register the new recipe with mechanical effect
    recipe = DiscoveredRecipe(
        inputs=sorted_targets,
        output_name=output_name,
        output_description=output_description,
        discovered_by=agent.id,
        discovered_tick=world_state.tick,
        times_built=0,
        effect_type=effect_type,
    )
    world_state.discovered_recipes.append(recipe)

    # Broadcast: all agents can now build this composition
    for a in world_state.agents.values():
        if recipe.output_name not in a.known_recipes:
            a.known_recipes.append(recipe.output_name)

    # Apply the recipe
    return _apply_recipe(agent, recipe, found_structures, tile, world_state)


def _find_recipe(
    sorted_inputs: list[str],
    world_state: WorldState,
) -> Optional[DiscoveredRecipe]:
    """Look up a known recipe by its sorted input list."""
    for recipe in world_state.discovered_recipes:
        if recipe.inputs == sorted_inputs:
            return recipe
    return None


def _apply_recipe(
    agent: AgentState,
    recipe: DiscoveredRecipe,
    input_structures: list[Structure],
    tile: Any,  # Tile
    world_state: WorldState,
) -> tuple[str, str]:
    """Apply a known recipe: remove input structures, create output.

    Returns (output_name, description).
    """
    # Remove input structures from tile
    for structure in input_structures:
        if structure in tile.structures:
            tile.structures.remove(structure)

    # Map effect_type to a real StructureType for mechanical effects
    struct_type = _EFFECT_TYPE_TO_STRUCTURE.get(recipe.effect_type, StructureType.MARKER)

    # Create the composed structure with real physics
    composed = Structure(
        structure_type=struct_type,
        builder_id=agent.id,
        built_tick=world_state.tick,
        health=1.0,
        custom_name=recipe.output_name,
        custom_description=recipe.output_description,
        composed_from=list(recipe.inputs),
    )
    tile.structures.append(composed)

    # Track
    recipe.times_built += 1
    if recipe.output_name not in agent.known_recipes:
        agent.known_recipes.append(recipe.output_name)

    logger.info(
        "Agent %d composed %s from %s at (%d, %d)",
        agent.id, recipe.output_name, recipe.inputs,
        tile.position.x, tile.position.y,
    )

    return recipe.output_name, recipe.output_description


async def _evaluate_composition(
    agent: AgentState,
    sorted_targets: list[str],
    found_structures: list[Structure],
    config: SimulationConfig,
    llm_client: Any,
) -> Optional[tuple[str, str]]:
    """Ask the LLM to evaluate whether combining these structures produces
    something meaningful.

    COMPOSITION evaluation (distinct from INNOVATION evaluation):
    "What does combining these existing things produce?"

    Returns (output_name, description) if the combination is meaningful,
    None if it's not.
    """
    # Build descriptions of the input structures
    input_descs: list[str] = []
    for s in found_structures:
        desc = s.structure_type.value
        if s.custom_name:
            desc = f"{s.custom_name} ({s.structure_type.value})"
        if s.custom_description:
            desc += f" — {s.custom_description}"
        input_descs.append(desc)

    prompt = f"""You are evaluating a COMPOSITION of existing structures in a world simulation.

An entity is attempting to combine these structures that exist on the same tile:
{chr(10).join(f'- {d}' for d in input_descs)}

The existing structure types in this world are: shelter (reduces degradation), storage (holds resources), marker (persistent message), path (reduces movement cost).

Question: Does combining {' + '.join(sorted_targets)} produce something functionally different from its parts? If yes, what is the resulting structure called and what does it do?

Rules:
- The result must be DIFFERENT from simply having both structures separately
- The result should be a plausible emergent property of the combination
- Be creative but grounded — the world is a resource-gathering survival simulation
- If the combination doesn't produce anything meaningful, say "NO_RESULT"

Respond in EXACTLY this format (no other text):
NAME: [name of resulting structure]
EFFECT: [one sentence describing what it does]
EFFECT_TYPE: [which existing mechanic it most closely resembles — one of: reduce_degradation, store_resources, persistent_message, reduce_movement_cost]

Or if the combination is meaningless:
NO_RESULT"""

    response = await llm_client.call_llm(prompt)
    return _parse_composition_response(response)


_VALID_EFFECT_TYPES = {"reduce_degradation", "store_resources", "persistent_message", "reduce_movement_cost"}

_EFFECT_TYPE_TO_STRUCTURE = {
    "reduce_degradation": StructureType.SHELTER,
    "store_resources": StructureType.STORAGE,
    "persistent_message": StructureType.MARKER,
    "reduce_movement_cost": StructureType.PATH,
}


def _parse_composition_response(response: str) -> Optional[tuple[str, str, str]]:
    """Parse the LLM's composition evaluation response.

    Returns (name, effect, effect_type) or None.
    """
    text = response.strip()

    if "NO_RESULT" in text.upper():
        return None

    import re
    name_match = re.search(r'NAME:\s*(.+)', text, re.IGNORECASE)
    effect_match = re.search(r'EFFECT:\s*(.+)', text, re.IGNORECASE)
    effect_type_match = re.search(r'EFFECT_TYPE:\s*(.+)', text, re.IGNORECASE)

    if name_match and effect_match:
        name = name_match.group(1).strip().rstrip(".")
        effect = effect_match.group(1).strip().rstrip(".")
        effect_type = "marker"
        if effect_type_match:
            raw_et = effect_type_match.group(1).strip().lower()
            if raw_et in _VALID_EFFECT_TYPES:
                effect_type = raw_et
        if name and effect:
            return name, effect, effect_type

    return None
