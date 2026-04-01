/**
 * TypeScript type definitions for the Agent Civilisation API.
 *
 * These interfaces match the Pydantic response models in src/api/schemas.py
 * exactly. Field names use snake_case to match the JSON response format.
 *
 * This file is the single source of truth for the frontend — import all
 * API types from here.
 */

// ---------------------------------------------------------------------------
// Bus Event Types (matches Python BusEventType enum)
// ---------------------------------------------------------------------------

export enum BusEventType {
  // Agentic loop events
  AGENTIC_TURN_START = "agentic_turn_start",
  REASONING_STEP = "reasoning_step",
  ACTION_TAKEN = "action_taken",
  OBSERVATION = "observation",
  GOAL_SET = "goal_set",
  GOAL_COMPLETED = "goal_completed",
  PLAN_UPDATED = "plan_updated",
  AGENTIC_TURN_END = "agentic_turn_end",

  // Communication
  MESSAGE_SENT = "message_sent",
  MESSAGE_RECEIVED = "message_received",

  // World events
  AGENT_ARRIVED = "agent_arrived",
  AGENT_MOVED = "agent_moved",
  AGENT_GATHERED = "agent_gathered",
  ENVIRONMENTAL_SHIFT = "environmental_shift",

  // Status changes
  DEGRADATION_CHANGED = "degradation_changed",
  WELLBEING_CHANGED = "wellbeing_changed",
  NEEDS_CRITICAL = "needs_critical",

  // Building / structures
  STRUCTURE_BUILT = "structure_built",
  STRUCTURE_DECAYED = "structure_decayed",
  STRUCTURE_DISCOVERED = "structure_discovered",
  RESOURCE_STORED = "resource_stored",
  RESOURCE_CONSUMED = "resource_consumed",
  MARKER_READ = "marker_read",

  // Composition & innovation
  COMPOSITION_DISCOVERED = "composition_discovered",
  COMPOSITION_FAILED = "composition_failed",
  INNOVATION_SUCCEEDED = "innovation_succeeded",
  INNOVATION_FAILED = "innovation_failed",

  // Collective rules
  RULE_PROPOSED = "rule_proposed",
  RULE_ACCEPTED = "rule_accepted",
  RULE_ESTABLISHED = "rule_established",

  // Specialisation
  SPECIALISATION_GAINED = "specialisation_gained",

  // Feedback loops
  MAINTENANCE_CONSUMED = "maintenance_consumed",
  CROWDING_EFFECT = "crowding_effect",

  // Deterministic behavior
  DETERMINISTIC_ACTION = "deterministic_action",

  // Tick-level
  TICK_START = "tick_start",
  TICK_END = "tick_end",

  // Watcher
  WATCHER_TICK_REPORT = "watcher_tick_report",
  WATCHER_NARRATIVE = "watcher_narrative",
  WATCHER_MILESTONE = "watcher_milestone",
}

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

export interface Position {
  x: number;
  y: number;
}

export interface ResourceSchema {
  resource_type: string;
  amount: number;
  max_amount: number;
  regeneration_rate: number;
  gathering_pressure: number;
}

export interface StructureSchema {
  structure_type: string;
  builder_id: number;
  built_tick: number;
  health: number;
  message: string | null;
  stored_resources: Record<string, number>;
  capacity: number;
  custom_name: string | null;
  custom_description: string | null;
  composed_from: string[] | null;
}

export interface StructureWithPosition extends StructureSchema {
  position: Position;
}

// ---------------------------------------------------------------------------
// Tiles
// ---------------------------------------------------------------------------

export interface TileSchema {
  position: Position;
  terrain: string;
  resources: Record<string, ResourceSchema>;
  structures: StructureSchema[];
}

// ---------------------------------------------------------------------------
// Agent capabilities & needs
// ---------------------------------------------------------------------------

export interface CapabilitiesSchema {
  perception_range: number;
  movement_speed: number;
  memory_capacity: number;
  base_perception_range: number;
  base_movement_speed: number;
  base_memory_capacity: number;
  degradation_ratio: number;
}

export interface NeedsSchema {
  levels: Record<string, number>;
}

// ---------------------------------------------------------------------------
// Memory & actions
// ---------------------------------------------------------------------------

export interface MemoryEntrySchema {
  tick: number;
  summary: string;
  importance: number;
  access_count: number;
}

export interface ActionSchema {
  type: string;
  direction: [number, number] | null;
  resource_type: string | null;
  message: string | null;
  target_agent_id: number | null;
  goal: string | null;
  structure_type: string | null;
  reasoning: string;
}

// ---------------------------------------------------------------------------
// Relationships
// ---------------------------------------------------------------------------

export interface RelationshipSchema {
  agent_id: number;
  interaction_count: number;
  positive_count: number;
  negative_count: number;
  last_interaction_tick: number;
  is_bonded: boolean;
}

// ---------------------------------------------------------------------------
// Agent responses
// ---------------------------------------------------------------------------

export interface AgentSummary {
  id: number;
  position: Position;
  wellbeing: number;
  curiosity: number;
  degradation_ratio: number;
  specialisations: string[];
  goals: string[];
  age: number;
  current_action_type: string | null;
  inventory_count: number;
  needs_critical: boolean;
}

export interface AgentDetailResponse {
  // All fields from AgentSummary
  id: number;
  position: Position;
  wellbeing: number;
  curiosity: number;
  degradation_ratio: number;
  specialisations: string[];
  goals: string[];
  age: number;
  current_action_type: string | null;
  inventory_count: number;
  needs_critical: boolean;

  // Detail-only fields
  needs: NeedsSchema;
  capabilities: CapabilitiesSchema;
  memories: MemoryEntrySchema[];
  plan: string[];
  inventory: string[];
  activity_counts: Record<string, number>;
  known_recipes: string[];
  relationships: RelationshipSchema[];
  current_action: ActionSchema | null;
  alive_since_tick: number;
}

export interface AgentListResponse {
  agents: AgentSummary[];
  total: number;
}

// ---------------------------------------------------------------------------
// Agent sub-resources
// ---------------------------------------------------------------------------

export interface MemoryListResponse {
  agent_id: number;
  memories: MemoryEntrySchema[];
}

export interface MessageSchema {
  sender_id: number;
  receiver_id: number;
  content: string;
  tick: number;
}

export interface InteractionListResponse {
  agent_id: number;
  messages: MessageSchema[];
}

// ---------------------------------------------------------------------------
// Structures
// ---------------------------------------------------------------------------

export interface StructureListResponse {
  structures: StructureWithPosition[];
}

export interface InnovationListResponse {
  innovations: StructureWithPosition[];
}

// ---------------------------------------------------------------------------
// Recipes
// ---------------------------------------------------------------------------

export interface DiscoveredRecipeSchema {
  inputs: string[];
  output_name: string;
  output_description: string;
  discovered_by: number;
  discovered_tick: number;
  times_built: number;
}

export interface RecipeListResponse {
  recipes: DiscoveredRecipeSchema[];
  total: number;
}

// ---------------------------------------------------------------------------
// Collective rules
// ---------------------------------------------------------------------------

export interface CollectiveRuleSchema {
  rule_id: number;
  text: string;
  proposed_by: number;
  proposed_tick: number;
  accepted_by: number[];
  ignored_by: number[];
  established: boolean;
  adoption_rate: number;
}

export interface RuleListResponse {
  rules: CollectiveRuleSchema[];
  total: number;
  established_count: number;
}

// ---------------------------------------------------------------------------
// Specialisation
// ---------------------------------------------------------------------------

export interface SpecialisationEntry {
  activity: string;
  agent_count: number;
  agent_ids: number[];
}

export interface SpecialisationResponse {
  specialisations: SpecialisationEntry[];
  total_specialised_agents: number;
}

// ---------------------------------------------------------------------------
// Chronicle (event log, milestones, narratives)
// ---------------------------------------------------------------------------

export interface ChronicleEntrySchema {
  type: string;
  tick: number;
  timestamp: number;
  data: Record<string, unknown>;
}

export interface ChronicleResponse {
  entries: ChronicleEntrySchema[];
  total: number;
}

export interface MilestoneSchema {
  name: string;
  tick: number;
  commentary: string;
}

export interface MilestoneListResponse {
  milestones: MilestoneSchema[];
}

export interface NarrativeSchema {
  tick: number;
  text: string;
}

export interface NarrativeListResponse {
  narratives: NarrativeSchema[];
}

// ---------------------------------------------------------------------------
// Stats & config
// ---------------------------------------------------------------------------

export interface StatsResponse {
  current_tick: number;
  total_agents: number;
  total_structures: number;
  total_innovations: number;
  total_compositions: number;
  total_recipes: number;
  total_rules: number;
  established_rules: number;
  total_milestones: number;
  total_specialised_agents: number;
  uptime_ticks: number;
}

export interface ConfigResponse {
  // World
  grid_width: number;
  grid_height: number;
  resource_types: string[];
  resource_distribution: string;
  resource_depletion_rate: number;
  resource_regeneration_rate: number;
  resource_cluster_count: number;
  resource_cluster_radius: number;
  resource_max_per_tile: number;
  terrain_types: string[];
  movement_cost: Record<string, number>;

  // Agents
  initial_agent_count: number;
  agent_perception_range: number;
  agent_communication_range: number;
  agent_base_movement_speed: number;
  agent_needs_depletion_rate: number;
  agent_gather_restore: number;
  agent_degradation_rate: number;
  agent_recovery_rate: number;
  agent_wellbeing_interaction_bonus: number;
  agent_wellbeing_decay_rate: number;
  agent_wellbeing_proximity_bonus: number;
  agent_memory_capacity: number;
  agent_memory_decay: boolean;
  agent_reflection_interval: number;

  // Population
  new_agent_interval: number;
  new_agent_spawn: string;

  // Environmental shifts
  enable_environmental_shifts: boolean;
  shift_interval: number;
  shift_severity: string;

  // Building
  agent_carry_capacity: number;
  structures: Record<string, unknown>;

  // Feedback loops
  enable_environmental_coevolution: boolean;
  heavy_gathering_regen_penalty: number;
  crowding_depletion_multiplier: number;
  structure_maintenance_cost: number;

  // Innovation & composition
  enable_innovation: boolean;
  enable_composition: boolean;
  innovation_evaluation_model: string;

  // Specialisation
  enable_specialisation: boolean;
  specialisation_threshold: number;
  specialisation_bonus: number;

  // Collective rules
  enable_collective_rules: boolean;
  rule_establishment_threshold: number;

  // Simulation
  ticks_per_real_minute: number;
  max_interactions_per_tick: number;
  max_concurrent_llm_calls: number;
  max_steps_per_agentic_turn: number;

  // LLM
  model_provider: string;
  model_name: string;
  api_key_env_var: string;
  llm_max_tokens: number;
  llm_temperature: number;

  // Watcher
  narrative_report_interval: number;
  enable_milestone_reports: boolean;

  // Persistence
  save_interval: number;
  save_path: string;
  log_path: string;

  // CLI
  log_level: string;
  show_agent_reasoning: boolean;
  show_conversations: boolean;
}

// ---------------------------------------------------------------------------
// World state (top-level snapshot)
// ---------------------------------------------------------------------------

export interface WorldStateResponse {
  tick: number;
  grid_width: number;
  grid_height: number;
  tiles: TileSchema[][];
  agents: AgentSummary[];
  stats: StatsResponse;
}

// ---------------------------------------------------------------------------
// WebSocket schemas
// ---------------------------------------------------------------------------

export interface BusEventSchema {
  type: string;
  tick: number;
  timestamp: number;
  agent_id: number | null;
  data: Record<string, unknown>;
}

/** Incoming WebSocket message (server -> client). */
export type WebSocketMessage = BusEventSchema;

/** Outgoing subscription filter (client -> server). */
export interface WebSocketSubscription {
  subscribe: string[];
}
