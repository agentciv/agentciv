"""Converters from simulation dataclass types to Pydantic API schemas.

These functions bridge the simulation engine's internal dataclasses
(defined in src/types.py) to the API's Pydantic response models
(defined in src/api/schemas.py). They handle all edge cases: None values,
computed properties (degradation_ratio, adoption_rate), and type coercions.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from src.api.schemas import (
    ActionSchema,
    AgentDetailResponse,
    AgentListResponse,
    AgentSummary,
    BusEventSchema,
    CapabilitiesSchema,
    ChronicleEntrySchema,
    ChronicleResponse,
    CollectiveRuleSchema,
    ConfigResponse,
    DiscoveredRecipeSchema,
    InnovationListResponse,
    InteractionListResponse,
    MemoryEntrySchema,
    MemoryListResponse,
    MessageSchema,
    MilestoneListResponse,
    MilestoneSchema,
    NarrativeListResponse,
    NarrativeSchema,
    NeedsSchema,
    PositionSchema,
    RecipeListResponse,
    RelationshipSchema,
    ResourceSchema,
    RuleListResponse,
    SpecialisationEntry,
    SpecialisationResponse,
    StatsResponse,
    StructureListResponse,
    StructureSchema,
    StructureWithPosition,
    TileSchema,
    WorldStateResponse,
)

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.types import (
        AgentState,
        BusEvent,
        CollectiveRule,
        DiscoveredRecipe,
        Message,
        MemoryEntry,
        Position,
        Resource,
        Structure,
        Tile,
        WorldState,
    )


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def position_to_schema(pos: Position) -> PositionSchema:
    """Convert a Position dataclass to a PositionSchema."""
    return PositionSchema(x=pos.x, y=pos.y)


def resource_to_schema(resource: Resource) -> ResourceSchema:
    """Convert a Resource dataclass to a ResourceSchema."""
    return ResourceSchema(
        resource_type=resource.resource_type,
        amount=resource.amount,
        max_amount=resource.max_amount,
        regeneration_rate=resource.regeneration_rate,
        gathering_pressure=resource.gathering_pressure,
    )


def structure_to_schema(structure: Structure, position: Position) -> StructureWithPosition:
    """Convert a Structure dataclass to a StructureWithPosition schema.

    The position is passed separately because structures don't store
    their own position -- they live on tiles.
    """
    return StructureWithPosition(
        structure_type=structure.structure_type.value if hasattr(structure.structure_type, 'value') else str(structure.structure_type),
        builder_id=structure.builder_id,
        built_tick=structure.built_tick,
        health=structure.health,
        message=structure.message,
        stored_resources=dict(structure.stored_resources) if structure.stored_resources else {},
        capacity=structure.capacity,
        custom_name=structure.custom_name,
        custom_description=structure.custom_description,
        composed_from=list(structure.composed_from) if structure.composed_from else None,
        position=position_to_schema(position),
    )


def _structure_to_base_schema(structure: Structure) -> StructureSchema:
    """Convert a Structure dataclass to a StructureSchema (without position)."""
    return StructureSchema(
        structure_type=structure.structure_type.value if hasattr(structure.structure_type, 'value') else str(structure.structure_type),
        builder_id=structure.builder_id,
        built_tick=structure.built_tick,
        health=structure.health,
        message=structure.message,
        stored_resources=dict(structure.stored_resources) if structure.stored_resources else {},
        capacity=structure.capacity,
        custom_name=structure.custom_name,
        custom_description=structure.custom_description,
        composed_from=list(structure.composed_from) if structure.composed_from else None,
    )


def tile_to_schema(tile: Tile) -> TileSchema:
    """Convert a Tile dataclass to a TileSchema."""
    return TileSchema(
        position=position_to_schema(tile.position),
        terrain=tile.terrain.value if hasattr(tile.terrain, 'value') else str(tile.terrain),
        resources={
            key: resource_to_schema(res) for key, res in tile.resources.items()
        },
        structures=[_structure_to_base_schema(s) for s in tile.structures],
    )


# ---------------------------------------------------------------------------
# Agent capabilities & needs
# ---------------------------------------------------------------------------

def capabilities_to_schema(caps: object) -> CapabilitiesSchema:
    """Convert a Capabilities dataclass to a CapabilitiesSchema.

    Calls the degradation_ratio() method to compute the derived field.
    """
    from src.types import Capabilities
    assert isinstance(caps, Capabilities)
    return CapabilitiesSchema(
        perception_range=caps.perception_range,
        movement_speed=caps.movement_speed,
        memory_capacity=caps.memory_capacity,
        base_perception_range=caps.base_perception_range,
        base_movement_speed=caps.base_movement_speed,
        base_memory_capacity=caps.base_memory_capacity,
        degradation_ratio=caps.degradation_ratio(),
    )


def needs_to_schema(needs: object) -> NeedsSchema:
    """Convert a NeedsState dataclass to a NeedsSchema."""
    from src.types import NeedsState
    assert isinstance(needs, NeedsState)
    return NeedsSchema(levels=dict(needs.levels))


# ---------------------------------------------------------------------------
# Memory & actions
# ---------------------------------------------------------------------------

def memory_to_schema(entry: MemoryEntry) -> MemoryEntrySchema:
    """Convert a MemoryEntry dataclass to a MemoryEntrySchema."""
    return MemoryEntrySchema(
        tick=entry.tick,
        summary=entry.summary,
        importance=entry.importance,
        access_count=entry.access_count,
    )


def action_to_schema(action: object) -> ActionSchema:
    """Convert an Action dataclass to an ActionSchema.

    Handles the ActionType enum by extracting its string value.
    """
    from src.types import Action
    assert isinstance(action, Action)
    return ActionSchema(
        type=action.type.value if hasattr(action.type, 'value') else str(action.type),
        direction=action.direction,
        resource_type=action.resource_type,
        message=action.message,
        target_agent_id=action.target_agent_id,
        goal=action.goal,
        structure_type=action.structure_type,
        reasoning=action.reasoning,
    )


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

def agent_to_summary(agent: AgentState) -> AgentSummary:
    """Convert an AgentState to a lightweight AgentSummary for list views."""
    return AgentSummary(
        id=agent.id,
        position=position_to_schema(agent.position),
        wellbeing=agent.wellbeing,
        curiosity=agent.curiosity,
        degradation_ratio=agent.capabilities.degradation_ratio(),
        specialisations=list(agent.specialisations),
        goals=list(agent.goals),
        age=agent.age,
        current_action_type=(
            agent.current_action.type.value
            if agent.current_action is not None and hasattr(agent.current_action.type, 'value')
            else (str(agent.current_action.type) if agent.current_action is not None else None)
        ),
        inventory_count=len(agent.inventory),
        needs_critical=agent.needs.any_critical(),
    )


def agent_to_detail(agent: AgentState) -> AgentDetailResponse:
    """Convert an AgentState to the full AgentDetailResponse."""
    return AgentDetailResponse(
        id=agent.id,
        position=position_to_schema(agent.position),
        wellbeing=agent.wellbeing,
        curiosity=agent.curiosity,
        degradation_ratio=agent.capabilities.degradation_ratio(),
        specialisations=list(agent.specialisations),
        goals=list(agent.goals),
        age=agent.age,
        current_action_type=(
            agent.current_action.type.value
            if agent.current_action is not None and hasattr(agent.current_action.type, 'value')
            else (str(agent.current_action.type) if agent.current_action is not None else None)
        ),
        inventory_count=len(agent.inventory),
        needs_critical=agent.needs.any_critical(),
        needs=needs_to_schema(agent.needs),
        capabilities=capabilities_to_schema(agent.capabilities),
        memories=[memory_to_schema(m) for m in agent.memories],
        plan=list(agent.plan),
        inventory=list(agent.inventory),
        activity_counts=dict(agent.activity_counts),
        known_recipes=list(agent.known_recipes),
        relationships=[
            RelationshipSchema(
                agent_id=other_id,
                interaction_count=rel.interaction_count,
                positive_count=rel.positive_count,
                negative_count=rel.negative_count,
                last_interaction_tick=rel.last_interaction_tick,
                is_bonded=rel.is_bonded,
            )
            for other_id, rel in agent.relationships.items()
        ],
        current_action=action_to_schema(agent.current_action) if agent.current_action else None,
        alive_since_tick=agent.alive_since_tick,
    )


def agents_to_list_response(agents: dict[int, AgentState]) -> AgentListResponse:
    """Convert a dict of agents to an AgentListResponse."""
    summaries = [agent_to_summary(a) for a in agents.values()]
    return AgentListResponse(agents=summaries, total=len(summaries))


# ---------------------------------------------------------------------------
# Agent sub-resources
# ---------------------------------------------------------------------------

def memories_to_response(agent: AgentState) -> MemoryListResponse:
    """Build a MemoryListResponse for a single agent."""
    return MemoryListResponse(
        agent_id=agent.id,
        memories=[memory_to_schema(m) for m in agent.memories],
    )


def message_to_schema(msg: Message) -> MessageSchema:
    """Convert a Message dataclass to a MessageSchema."""
    return MessageSchema(
        sender_id=msg.sender_id,
        receiver_id=msg.receiver_id,
        content=msg.content,
        tick=msg.tick,
    )


def interactions_to_response(
    agent_id: int,
    messages: list[Message],
) -> InteractionListResponse:
    """Build an InteractionListResponse for a single agent.

    Filters messages to those where the agent is sender or receiver.
    """
    relevant = [
        m for m in messages
        if m.sender_id == agent_id or m.receiver_id == agent_id or m.receiver_id == -1
    ]
    return InteractionListResponse(
        agent_id=agent_id,
        messages=[message_to_schema(m) for m in relevant],
    )


# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------

def structures_to_list_response(world_state: WorldState) -> StructureListResponse:
    """Collect all structures from the grid into a flat list with positions."""
    result: list[StructureWithPosition] = []
    for col in world_state.tiles:
        for tile in col:
            for struct in tile.structures:
                result.append(structure_to_schema(struct, tile.position))
    return StructureListResponse(structures=result)


def innovations_to_list_response(world_state: WorldState) -> InnovationListResponse:
    """Collect structures with custom_name (agent innovations)."""
    result: list[StructureWithPosition] = []
    for col in world_state.tiles:
        for tile in col:
            for struct in tile.structures:
                if struct.custom_name is not None:
                    result.append(structure_to_schema(struct, tile.position))
    return InnovationListResponse(innovations=result)


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

def recipe_to_schema(recipe: DiscoveredRecipe) -> DiscoveredRecipeSchema:
    """Convert a DiscoveredRecipe dataclass to a DiscoveredRecipeSchema."""
    return DiscoveredRecipeSchema(
        inputs=list(recipe.inputs),
        output_name=recipe.output_name,
        output_description=recipe.output_description,
        discovered_by=recipe.discovered_by,
        discovered_tick=recipe.discovered_tick,
        times_built=recipe.times_built,
    )


def recipes_to_list_response(recipes: list[DiscoveredRecipe]) -> RecipeListResponse:
    """Convert a list of DiscoveredRecipe to a RecipeListResponse."""
    schemas = [recipe_to_schema(r) for r in recipes]
    return RecipeListResponse(recipes=schemas, total=len(schemas))


# ---------------------------------------------------------------------------
# Collective rules
# ---------------------------------------------------------------------------

def rule_to_schema(rule: CollectiveRule) -> CollectiveRuleSchema:
    """Convert a CollectiveRule dataclass to a CollectiveRuleSchema.

    Calls the adoption_rate property to compute the derived field.
    """
    return CollectiveRuleSchema(
        rule_id=rule.rule_id,
        text=rule.text,
        proposed_by=rule.proposed_by,
        proposed_tick=rule.proposed_tick,
        accepted_by=list(rule.accepted_by),
        ignored_by=list(rule.ignored_by),
        established=rule.established,
        adoption_rate=rule.adoption_rate,
    )


def rules_to_list_response(rules: list[CollectiveRule]) -> RuleListResponse:
    """Convert a list of CollectiveRule to a RuleListResponse."""
    schemas = [rule_to_schema(r) for r in rules]
    established_count = sum(1 for r in rules if r.established)
    return RuleListResponse(
        rules=schemas,
        total=len(schemas),
        established_count=established_count,
    )


# ---------------------------------------------------------------------------
# Specialisation
# ---------------------------------------------------------------------------

def specialisations_to_response(agents: dict[int, AgentState]) -> SpecialisationResponse:
    """Aggregate specialisation data across all agents."""
    activity_map: dict[str, list[int]] = defaultdict(list)
    specialised_agent_ids: set[int] = set()

    for agent in agents.values():
        for spec in agent.specialisations:
            activity_map[spec].append(agent.id)
            specialised_agent_ids.add(agent.id)

    entries = [
        SpecialisationEntry(
            activity=activity,
            agent_count=len(agent_ids),
            agent_ids=sorted(agent_ids),
        )
        for activity, agent_ids in sorted(activity_map.items())
    ]

    return SpecialisationResponse(
        specialisations=entries,
        total_specialised_agents=len(specialised_agent_ids),
    )


# ---------------------------------------------------------------------------
# Chronicle (event bus log)
# ---------------------------------------------------------------------------

def bus_event_to_chronicle_entry(event: BusEvent) -> ChronicleEntrySchema:
    """Convert a BusEvent to a ChronicleEntrySchema."""
    return ChronicleEntrySchema(
        type=event.type.value if hasattr(event.type, 'value') else str(event.type),
        tick=event.tick,
        timestamp=event.timestamp,
        data=dict(event.data) if event.data else {},
    )


def chronicle_to_response(
    events: list[BusEvent],
    offset: int = 0,
    limit: int | None = None,
) -> ChronicleResponse:
    """Build a paginated ChronicleResponse from bus events."""
    total = len(events)
    sliced = events[offset:] if limit is None else events[offset:offset + limit]
    entries = [bus_event_to_chronicle_entry(e) for e in sliced]
    return ChronicleResponse(entries=entries, total=total)


def milestones_to_response(events: list[BusEvent]) -> MilestoneListResponse:
    """Extract milestone events from the bus log.

    Milestones are BusEvents with type WATCHER_MILESTONE.
    The data dict is expected to contain 'name' and 'commentary'.
    """
    from src.types import BusEventType

    milestones: list[MilestoneSchema] = []
    for event in events:
        if event.type == BusEventType.WATCHER_MILESTONE:
            milestones.append(MilestoneSchema(
                name=event.data.get("name", "Unknown"),
                tick=event.tick,
                commentary=event.data.get("commentary", ""),
            ))
    return MilestoneListResponse(milestones=milestones)


def narratives_to_response(events: list[BusEvent]) -> NarrativeListResponse:
    """Extract narrative events from the bus log.

    Narratives are BusEvents with type WATCHER_NARRATIVE.
    The data dict is expected to contain 'text'.
    """
    from src.types import BusEventType

    narratives: list[NarrativeSchema] = []
    for event in events:
        if event.type == BusEventType.WATCHER_NARRATIVE:
            narratives.append(NarrativeSchema(
                tick=event.tick,
                text=event.data.get("text", ""),
            ))
    return NarrativeListResponse(narratives=narratives)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def world_state_to_stats(world_state: WorldState) -> StatsResponse:
    """Compute aggregate statistics from the current world state."""
    total_structures = 0
    total_innovations = 0
    total_compositions = 0

    for col in world_state.tiles:
        for tile in col:
            for struct in tile.structures:
                total_structures += 1
                if struct.custom_name is not None:
                    total_innovations += 1
                if struct.composed_from is not None:
                    total_compositions += 1

    total_specialised = sum(
        1 for a in world_state.agents.values() if len(a.specialisations) > 0
    )

    established_rules = sum(
        1 for r in world_state.collective_rules if r.established
    )

    # Count milestones from the event log
    from src.types import BusEventType
    total_milestones = sum(
        1 for e in world_state.event_log
        if hasattr(e, 'type') and (
            (hasattr(e.type, 'value') and e.type.value == BusEventType.WATCHER_MILESTONE.value)
            if hasattr(e.type, 'value') else False
        )
    )

    return StatsResponse(
        current_tick=world_state.tick,
        total_agents=len(world_state.agents),
        total_structures=total_structures,
        total_innovations=total_innovations,
        total_compositions=total_compositions,
        total_recipes=len(world_state.discovered_recipes),
        total_rules=len(world_state.collective_rules),
        established_rules=established_rules,
        total_milestones=total_milestones,
        total_specialised_agents=total_specialised,
        uptime_ticks=world_state.tick,
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def config_to_response(config: SimulationConfig) -> ConfigResponse:
    """Convert a SimulationConfig dataclass to a ConfigResponse."""
    return ConfigResponse(
        grid_width=config.grid_width,
        grid_height=config.grid_height,
        resource_types=list(config.resource_types),
        resource_distribution=config.resource_distribution,
        resource_depletion_rate=config.resource_depletion_rate,
        resource_regeneration_rate=config.resource_regeneration_rate,
        resource_cluster_count=config.resource_cluster_count,
        resource_cluster_radius=config.resource_cluster_radius,
        resource_max_per_tile=config.resource_max_per_tile,
        terrain_types=list(config.terrain_types),
        movement_cost=dict(config.movement_cost),
        initial_agent_count=config.initial_agent_count,
        agent_perception_range=config.agent_perception_range,
        agent_communication_range=config.agent_communication_range,
        agent_base_movement_speed=config.agent_base_movement_speed,
        agent_needs_depletion_rate=config.agent_needs_depletion_rate,
        agent_gather_restore=config.agent_gather_restore,
        agent_degradation_rate=config.agent_degradation_rate,
        agent_recovery_rate=config.agent_recovery_rate,
        agent_wellbeing_interaction_bonus=config.agent_wellbeing_interaction_bonus,
        agent_wellbeing_decay_rate=config.agent_wellbeing_decay_rate,
        agent_wellbeing_proximity_bonus=config.agent_wellbeing_proximity_bonus,
        agent_memory_capacity=config.agent_memory_capacity,
        agent_memory_decay=config.agent_memory_decay,
        agent_reflection_interval=config.agent_reflection_interval,
        new_agent_interval=config.new_agent_interval,
        new_agent_spawn=config.new_agent_spawn,
        enable_environmental_shifts=config.enable_environmental_shifts,
        shift_interval=config.shift_interval,
        shift_severity=config.shift_severity,
        agent_carry_capacity=config.agent_carry_capacity,
        structures=dict(config.structures),
        enable_environmental_coevolution=config.enable_environmental_coevolution,
        heavy_gathering_regen_penalty=config.heavy_gathering_regen_penalty,
        crowding_depletion_multiplier=config.crowding_depletion_multiplier,
        structure_maintenance_cost=config.structure_maintenance_cost,
        enable_innovation=config.enable_innovation,
        enable_composition=config.enable_composition,
        innovation_evaluation_model=config.innovation_evaluation_model,
        enable_specialisation=config.enable_specialisation,
        specialisation_threshold=config.specialisation_threshold,
        specialisation_bonus=config.specialisation_bonus,
        enable_collective_rules=config.enable_collective_rules,
        rule_establishment_threshold=config.rule_establishment_threshold,
        ticks_per_real_minute=config.ticks_per_real_minute,
        max_interactions_per_tick=config.max_interactions_per_tick,
        max_concurrent_llm_calls=config.max_concurrent_llm_calls,
        max_steps_per_agentic_turn=config.max_steps_per_agentic_turn,
        model_provider=config.model_provider,
        model_name=config.model_name,
        api_key_env_var=config.api_key_env_var,
        llm_max_tokens=config.llm_max_tokens,
        llm_temperature=config.llm_temperature,
        narrative_report_interval=config.narrative_report_interval,
        enable_milestone_reports=config.enable_milestone_reports,
        save_interval=config.save_interval,
        save_path=config.save_path,
        log_path=config.log_path,
        log_level=config.log_level,
        show_agent_reasoning=config.show_agent_reasoning,
        show_conversations=config.show_conversations,
    )


# ---------------------------------------------------------------------------
# World state (top-level)
# ---------------------------------------------------------------------------

def world_state_to_response(world_state: WorldState) -> WorldStateResponse:
    """Convert a full WorldState to the top-level WorldStateResponse.

    This is the main serialization entrypoint. It converts the entire
    grid, all agents (as summaries), and computes aggregate stats.
    """
    tiles_schema: list[list[TileSchema]] = []
    for col in world_state.tiles:
        col_schemas: list[TileSchema] = []
        for tile in col:
            col_schemas.append(tile_to_schema(tile))
        tiles_schema.append(col_schemas)

    agent_summaries = [agent_to_summary(a) for a in world_state.agents.values()]
    stats = world_state_to_stats(world_state)

    return WorldStateResponse(
        tick=world_state.tick,
        grid_width=world_state.grid_width,
        grid_height=world_state.grid_height,
        tiles=tiles_schema,
        agents=agent_summaries,
        stats=stats,
    )


# ---------------------------------------------------------------------------
# Bus events (WebSocket)
# ---------------------------------------------------------------------------

def bus_event_to_schema(event: BusEvent) -> BusEventSchema:
    """Convert a BusEvent dataclass to a BusEventSchema for WebSocket push."""
    return BusEventSchema(
        type=event.type.value if hasattr(event.type, 'value') else str(event.type),
        tick=event.tick,
        timestamp=event.timestamp,
        agent_id=event.agent_id,
        data=dict(event.data) if event.data else {},
    )
