"""Pydantic v2 response models for the Agent Civilisation REST API.

These schemas define the JSON contract between the Python simulation backend
and all consumers (fishbowl frontend, website, CLI tools). Every REST endpoint
returns one of these models. WebSocket events use BusEventSchema.

All field names use snake_case to match the simulation's internal types.
Frontends consume the JSON as-is (no camelCase transform).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

class PositionSchema(BaseModel):
    """A grid coordinate."""
    model_config = ConfigDict(from_attributes=True)

    x: int
    y: int


class ResourceSchema(BaseModel):
    """A single resource on a tile."""
    model_config = ConfigDict(from_attributes=True)

    resource_type: str
    amount: float
    max_amount: float
    regeneration_rate: float
    gathering_pressure: float


class StructureSchema(BaseModel):
    """A persistent structure built by an agent."""
    model_config = ConfigDict(from_attributes=True)

    structure_type: str
    builder_id: int
    built_tick: int
    health: float
    message: str | None = None
    stored_resources: dict[str, float] = Field(default_factory=dict)
    capacity: float = 10.0
    custom_name: str | None = None
    custom_description: str | None = None
    composed_from: list[str] | None = None


class StructureWithPosition(StructureSchema):
    """Structure with its tile position for list endpoints."""
    position: PositionSchema


# ---------------------------------------------------------------------------
# Tiles
# ---------------------------------------------------------------------------

class TileSchema(BaseModel):
    """A single tile on the world grid."""
    model_config = ConfigDict(from_attributes=True)

    position: PositionSchema
    terrain: str
    resources: dict[str, ResourceSchema] = Field(default_factory=dict)
    structures: list[StructureSchema] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent capabilities & needs
# ---------------------------------------------------------------------------

class CapabilitiesSchema(BaseModel):
    """Agent capabilities with degradation state.

    degradation_ratio is computed: 0.0 = fully healthy, 1.0 = maximally degraded.
    """
    model_config = ConfigDict(from_attributes=True)

    perception_range: float
    movement_speed: float
    memory_capacity: int
    base_perception_range: float
    base_movement_speed: float
    base_memory_capacity: int
    degradation_ratio: float


class NeedsSchema(BaseModel):
    """Agent needs keyed by resource type, each in [0.0, 1.0]."""
    model_config = ConfigDict(from_attributes=True)

    levels: dict[str, float]


# ---------------------------------------------------------------------------
# Memory & actions
# ---------------------------------------------------------------------------

class MemoryEntrySchema(BaseModel):
    """A single memory entry in an agent's memory bank."""
    model_config = ConfigDict(from_attributes=True)

    tick: int
    summary: str
    importance: float
    access_count: int


class ActionSchema(BaseModel):
    """An action taken or being taken by an agent."""
    model_config = ConfigDict(from_attributes=True)

    type: str
    direction: tuple[int, int] | None = None
    resource_type: str | None = None
    message: str | None = None
    target_agent_id: int | None = None
    goal: str | None = None
    structure_type: str | None = None
    reasoning: str = ""


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------

class RelationshipSchema(BaseModel):
    """A relationship between an agent and another agent."""
    model_config = ConfigDict(from_attributes=True)

    agent_id: int
    interaction_count: int = 0
    positive_count: int = 0
    negative_count: int = 0
    last_interaction_tick: int = 0
    is_bonded: bool = False


# ---------------------------------------------------------------------------
# Agent responses
# ---------------------------------------------------------------------------

class AgentSummary(BaseModel):
    """Lightweight agent representation for list views and world state."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: PositionSchema
    wellbeing: float
    curiosity: float = 0.5
    degradation_ratio: float
    specialisations: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    age: int = 0
    current_action_type: str | None = None
    inventory_count: int = 0
    needs_critical: bool = False


class AgentDetailResponse(BaseModel):
    """Full agent detail including memories, plan, and capabilities."""
    model_config = ConfigDict(from_attributes=True)

    # All fields from AgentSummary
    id: int
    position: PositionSchema
    wellbeing: float
    curiosity: float = 0.5
    degradation_ratio: float
    specialisations: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    age: int = 0
    current_action_type: str | None = None
    inventory_count: int = 0
    needs_critical: bool = False

    # Detail-only fields
    needs: NeedsSchema
    capabilities: CapabilitiesSchema
    memories: list[MemoryEntrySchema] = Field(default_factory=list)
    plan: list[str] = Field(default_factory=list)
    inventory: list[str] = Field(default_factory=list)
    activity_counts: dict[str, int] = Field(default_factory=dict)
    known_recipes: list[str] = Field(default_factory=list)
    relationships: list[RelationshipSchema] = Field(default_factory=list)
    current_action: ActionSchema | None = None
    alive_since_tick: int = 0


class AgentListResponse(BaseModel):
    """Paginated list of agent summaries."""
    agents: list[AgentSummary]
    total: int


# ---------------------------------------------------------------------------
# Agent sub-resources
# ---------------------------------------------------------------------------

class MemoryListResponse(BaseModel):
    """All memories for a single agent."""
    agent_id: int
    memories: list[MemoryEntrySchema]


class MessageSchema(BaseModel):
    """A message exchanged between agents."""
    model_config = ConfigDict(from_attributes=True)

    sender_id: int
    receiver_id: int
    content: str
    tick: int


class InteractionListResponse(BaseModel):
    """Messages involving a specific agent."""
    agent_id: int
    messages: list[MessageSchema]


# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------

class StructureListResponse(BaseModel):
    """All structures in the world with their positions."""
    structures: list[StructureWithPosition]


class InnovationListResponse(BaseModel):
    """Structures that have a custom name (agent innovations)."""
    innovations: list[StructureWithPosition]


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

class DiscoveredRecipeSchema(BaseModel):
    """A composition recipe discovered by agents."""
    model_config = ConfigDict(from_attributes=True)

    inputs: list[str]
    output_name: str
    output_description: str
    discovered_by: int
    discovered_tick: int
    times_built: int = 0


class RecipeListResponse(BaseModel):
    """All discovered composition recipes."""
    recipes: list[DiscoveredRecipeSchema]
    total: int


# ---------------------------------------------------------------------------
# Collective rules
# ---------------------------------------------------------------------------

class CollectiveRuleSchema(BaseModel):
    """A collective rule proposed by an agent, with adoption tracking.

    adoption_rate is computed: fraction of agents who have seen this rule
    and accepted it.
    """
    model_config = ConfigDict(from_attributes=True)

    rule_id: int
    text: str
    proposed_by: int
    proposed_tick: int
    accepted_by: list[int] = Field(default_factory=list)
    ignored_by: list[int] = Field(default_factory=list)
    established: bool = False
    adoption_rate: float = 0.0


class RuleListResponse(BaseModel):
    """All collective rules with summary counts."""
    rules: list[CollectiveRuleSchema]
    total: int
    established_count: int


# ---------------------------------------------------------------------------
# Specialisation
# ---------------------------------------------------------------------------

class SpecialisationEntry(BaseModel):
    """A single specialisation activity and the agents who have it."""
    activity: str
    agent_count: int
    agent_ids: list[int]


class SpecialisationResponse(BaseModel):
    """Aggregated specialisation data across all agents."""
    specialisations: list[SpecialisationEntry]
    total_specialised_agents: int


# ---------------------------------------------------------------------------
# Chronicle (event log, milestones, narratives)
# ---------------------------------------------------------------------------

class ChronicleEntrySchema(BaseModel):
    """A single event from the simulation chronicle."""
    model_config = ConfigDict(from_attributes=True)

    type: str
    tick: int
    timestamp: float
    data: dict


class ChronicleResponse(BaseModel):
    """Paginated chronicle entries."""
    entries: list[ChronicleEntrySchema]
    total: int


class MilestoneSchema(BaseModel):
    """A significant event identified by the watcher."""
    name: str
    tick: int
    commentary: str


class MilestoneListResponse(BaseModel):
    """All milestones reached so far."""
    milestones: list[MilestoneSchema]


class NarrativeSchema(BaseModel):
    """A narrative passage generated by the watcher."""
    tick: int
    text: str


class NarrativeListResponse(BaseModel):
    """All narrative passages generated so far."""
    narratives: list[NarrativeSchema]


# ---------------------------------------------------------------------------
# Stats & config
# ---------------------------------------------------------------------------

class StatsResponse(BaseModel):
    """Aggregate simulation statistics."""
    current_tick: int
    total_agents: int
    total_structures: int
    total_innovations: int
    total_compositions: int
    total_recipes: int
    total_rules: int
    established_rules: int
    total_milestones: int
    total_specialised_agents: int
    uptime_ticks: int


class ConfigResponse(BaseModel):
    """Full simulation configuration (read-only)."""
    model_config = ConfigDict(from_attributes=True)

    # World
    grid_width: int
    grid_height: int
    resource_types: list[str]
    resource_distribution: str
    resource_depletion_rate: float
    resource_regeneration_rate: float
    resource_cluster_count: int
    resource_cluster_radius: int
    resource_max_per_tile: float
    terrain_types: list[str]
    movement_cost: dict[str, int]

    # Agents
    initial_agent_count: int
    agent_perception_range: int
    agent_communication_range: int
    agent_base_movement_speed: float
    agent_needs_depletion_rate: float
    agent_gather_restore: float
    agent_degradation_rate: float
    agent_recovery_rate: float
    agent_wellbeing_interaction_bonus: float
    agent_wellbeing_decay_rate: float
    agent_wellbeing_proximity_bonus: float
    agent_memory_capacity: int
    agent_memory_decay: bool
    agent_reflection_interval: int

    # Population
    new_agent_interval: int
    new_agent_spawn: str

    # Environmental shifts
    enable_environmental_shifts: bool
    shift_interval: int
    shift_severity: str

    # Building
    agent_carry_capacity: int
    structures: dict

    # Feedback loops
    enable_environmental_coevolution: bool
    heavy_gathering_regen_penalty: float
    crowding_depletion_multiplier: float
    structure_maintenance_cost: float

    # Innovation & composition
    enable_innovation: bool
    enable_composition: bool
    innovation_evaluation_model: str

    # Specialisation
    enable_specialisation: bool
    specialisation_threshold: int
    specialisation_bonus: float

    # Collective rules
    enable_collective_rules: bool
    rule_establishment_threshold: float

    # Simulation
    ticks_per_real_minute: float
    max_interactions_per_tick: int
    max_concurrent_llm_calls: int
    max_steps_per_agentic_turn: int

    # LLM
    model_provider: str
    model_name: str
    api_key_env_var: str
    llm_max_tokens: int
    llm_temperature: float

    # Watcher
    narrative_report_interval: int
    enable_milestone_reports: bool

    # Persistence
    save_interval: int
    save_path: str
    log_path: str

    # CLI
    log_level: str
    show_agent_reasoning: bool
    show_conversations: bool


# ---------------------------------------------------------------------------
# World state (top-level snapshot)
# ---------------------------------------------------------------------------

class WorldStateResponse(BaseModel):
    """Full world state snapshot, used for both current state and history."""
    tick: int
    grid_width: int
    grid_height: int
    tiles: list[list[TileSchema]]
    agents: list[AgentSummary]
    stats: StatsResponse


# ---------------------------------------------------------------------------
# WebSocket schemas
# ---------------------------------------------------------------------------

class BusEventSchema(BaseModel):
    """A simulation event pushed over WebSocket."""
    model_config = ConfigDict(from_attributes=True)

    type: str
    tick: int
    timestamp: float
    agent_id: int | None = None
    data: dict = Field(default_factory=dict)


class WebSocketSubscription(BaseModel):
    """Client message to filter which event types to receive.

    Send this over the WebSocket connection to subscribe to specific
    BusEventType values. An empty list means subscribe to everything.
    """
    subscribe: list[str] = Field(default_factory=list)
