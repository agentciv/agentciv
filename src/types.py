"""Shared types for Agent Civilisation.

This module defines the data contracts between the simulation engine and agent
runtime. Both systems import from here — never define these types locally.

Key flows documented here:
- Capability degradation/recovery (engine applies per tick, runtime reads for behavior)
- Wellbeing dynamics (engine applies decay, runtime triggers bonuses, both read level)
- Needs depletion (engine depletes per tick, runtime checks for LLM triggers)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, ClassVar, Optional


# ---------------------------------------------------------------------------
# Position & Grid
# ---------------------------------------------------------------------------

@dataclass
class Position:
    x: int
    y: int

    def distance_to(self, other: Position) -> float:
        """Chebyshev distance (king-move distance on grid)."""
        return max(abs(self.x - other.x), abs(self.y - other.y))

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Position):
            return NotImplemented
        return self.x == other.x and self.y == other.y


class TerrainType(str, Enum):
    PLAIN = "plain"
    ROCKY = "rocky"
    DENSE = "dense"


class StructureType(str, Enum):
    SHELTER = "shelter"
    STORAGE = "storage"
    MARKER = "marker"
    PATH = "path"


@dataclass
class Resource:
    resource_type: str      # e.g. "water", "food", "material"
    amount: float           # current amount on this tile [0.0, max_amount]
    max_amount: float       # tile capacity
    regeneration_rate: float  # amount restored per tick
    gathering_pressure: float = 0.0  # accumulated gathering intensity — environmental co-evolution


@dataclass
class Structure:
    """A persistent structure built by an agent on a tile."""
    structure_type: StructureType
    builder_id: int          # agent who built it
    built_tick: int          # when it was built
    health: float = 1.0      # [0.0, 1.0] — decays over time, removed at 0
    message: Optional[str] = None       # for markers: persistent text
    stored_resources: dict[str, float] = field(default_factory=dict)  # for storage
    capacity: float = 10.0   # for storage: max total resources held
    # Innovation-created structures get a custom name and description
    custom_name: Optional[str] = None
    custom_description: Optional[str] = None
    # Composition: which structure types were combined to create this
    composed_from: Optional[list[str]] = None
    # Innovation effect type: custom mechanical effect identifier
    # None for base structures (shelter/storage/marker/path) — they use structure_type.
    # For innovations: "boost_gathering", "boost_regeneration", "reduce_need_depletion",
    # "boost_wellbeing", "extend_perception", or one of the 4 base effect strings.
    effect_type: Optional[str] = None


# ---------------------------------------------------------------------------
# Discovered Recipes — composition engine registry
# ---------------------------------------------------------------------------

@dataclass
class DiscoveredRecipe:
    """A composition recipe discovered by agents through experimentation.

    When agents combine existing structures and the LLM evaluates the
    combination as producing something meaningful, a DiscoveredRecipe is
    created and added to the world registry. Future agents can then
    build the same composition without re-evaluation.
    """
    inputs: list[str]          # sorted list of StructureType values combined
    output_name: str           # name of the resulting structure
    output_description: str    # what it does (from LLM evaluation)
    discovered_by: int         # agent_id who first discovered it
    discovered_tick: int       # when it was discovered
    times_built: int = 0       # how many times this recipe has been used
    # Mechanical effect: maps to a base structure type's physics
    # One of: "shelter", "storage", "marker", "path" — determines what the
    # structure actually DOES in the engine (reduce degradation, store resources, etc.)
    effect_type: str = "marker"


# ---------------------------------------------------------------------------
# Collective Rules — emergent governance
# ---------------------------------------------------------------------------

@dataclass
class CollectiveRule:
    """A rule proposed by an agent and tracked for adoption.

    Rules are free-text norms that agents can propose, accept, or ignore.
    When adoption_rate crosses the establishment threshold, the rule
    becomes part of every agent's perception context — a seed of governance.
    """
    rule_id: int
    text: str                  # the rule content, proposed by an agent
    proposed_by: int           # agent_id who proposed it
    proposed_tick: int         # when it was proposed
    accepted_by: list[int] = field(default_factory=list)    # agent_ids who accepted
    ignored_by: list[int] = field(default_factory=list)     # agent_ids who explicitly ignored
    established: bool = False  # True once adoption_rate >= threshold

    @property
    def adoption_rate(self) -> float:
        """Fraction of agents who have seen this rule and accepted it."""
        total_seen = len(self.accepted_by) + len(self.ignored_by)
        if total_seen == 0:
            return 0.0
        return len(self.accepted_by) / total_seen


@dataclass
class Tile:
    position: Position
    terrain: TerrainType
    resources: dict[str, Resource] = field(default_factory=dict)
    structures: list[Structure] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent Capabilities — degradation & recovery
# ---------------------------------------------------------------------------
#
# FLOW (managed by the tick loop in engine/tick.py):
#
# Each tick:
#   1. Deplete agent needs (needs -= config.agent_needs_depletion_rate)
#   2. Check needs against thresholds:
#      - If ANY need < DEGRADATION_THRESHOLD:
#          each capability moves toward its minimum at config.agent_degradation_rate
#          new_val = current - (current - minimum) * degradation_rate
#      - If ALL needs >= RECOVERY_THRESHOLD:
#          each capability moves toward its base at config.agent_recovery_rate
#          new_val = current + (base - current) * recovery_rate
#      - Between thresholds: no change (hysteresis band prevents jitter)
#   3. Clamp capabilities to [minimum, base]
#
# Recovery is faster than degradation by default config values (0.02 vs 0.01).
# Agents are NEVER fully incapacitated — minimums ensure they can always
# perceive, move (slowly), and retain some memory.

@dataclass
class Capabilities:
    """Agent capabilities that degrade when needs are unmet and recover when met."""

    perception_range: float     # tiles visible in each direction
    movement_speed: float       # max tiles movable per tick
    memory_capacity: int        # max memory entries before eviction

    base_perception_range: float
    base_movement_speed: float
    base_memory_capacity: int

    # Floors — agents are never fully incapacitated (no death principle)
    MIN_PERCEPTION_RANGE: ClassVar[float] = 1.0
    MIN_MOVEMENT_SPEED: ClassVar[float] = 0.5
    MIN_MEMORY_CAPACITY: ClassVar[int] = 10

    # Thresholds for when degradation/recovery kicks in
    DEGRADATION_THRESHOLD: ClassVar[float] = 0.3   # any need below this → degrade
    RECOVERY_THRESHOLD: ClassVar[float] = 0.5       # all needs above this → recover

    def degradation_ratio(self) -> float:
        """0.0 = fully healthy, 1.0 = maximally degraded."""
        if self.base_perception_range <= self.MIN_PERCEPTION_RANGE:
            return 0.0
        total_range = self.base_perception_range - self.MIN_PERCEPTION_RANGE
        current_loss = self.base_perception_range - self.perception_range
        return min(1.0, max(0.0, current_loss / total_range))

    @classmethod
    def create_healthy(
        cls,
        perception_range: float,
        movement_speed: float,
        memory_capacity: int,
    ) -> Capabilities:
        """Create fully healthy capabilities from config base values."""
        return cls(
            perception_range=perception_range,
            movement_speed=movement_speed,
            memory_capacity=memory_capacity,
            base_perception_range=perception_range,
            base_movement_speed=movement_speed,
            base_memory_capacity=memory_capacity,
        )


# ---------------------------------------------------------------------------
# Agent Needs
# ---------------------------------------------------------------------------
#
# Each resource type maps to a need level in [0.0, 1.0].
# 1.0 = fully satisfied, 0.0 = completely unmet.
# Needs deplete each tick at config.agent_needs_depletion_rate.
# Gathering a resource restores the corresponding need.

@dataclass
class NeedsState:
    levels: dict[str, float] = field(default_factory=dict)

    def lowest(self) -> tuple[str, float]:
        """Most urgent need (type, level)."""
        return min(self.levels.items(), key=lambda x: x[1])

    def any_critical(self, threshold: float = Capabilities.DEGRADATION_THRESHOLD) -> bool:
        """Whether any need is below the degradation threshold."""
        return any(v < threshold for v in self.levels.values())

    def all_healthy(self, threshold: float = Capabilities.RECOVERY_THRESHOLD) -> bool:
        """Whether all needs are above the recovery threshold."""
        return all(v >= threshold for v in self.levels.values())

    def satisfy(self, resource_type: str, amount: float) -> None:
        """Increase a need level (clamped to 1.0)."""
        if resource_type in self.levels:
            self.levels[resource_type] = min(1.0, self.levels[resource_type] + amount)

    def deplete_all(self, rate: float) -> None:
        """Deplete all needs by rate (clamped to 0.0)."""
        for k in self.levels:
            self.levels[k] = max(0.0, self.levels[k] - rate)

    @classmethod
    def create_full(cls, resource_types: list[str]) -> NeedsState:
        """All needs start fully satisfied."""
        return cls(levels={rt: 1.0 for rt in resource_types})


# ---------------------------------------------------------------------------
# Wellbeing
# ---------------------------------------------------------------------------
#
# FLOW (dual-drive system):
#
# Wellbeing is a float [0.0, 1.0] stored on AgentState.
#
# Increases:
#   - Successful communication with another agent: +config.agent_wellbeing_interaction_bonus
#   - Proximity to other agents during a tick: +small bonus (optional, configurable)
#   - Cooperative action (e.g. sharing resource info): +bonus
#
# Decreases:
#   - Natural decay each tick: -config.agent_wellbeing_decay_rate
#   - Does NOT decrease from unmet needs (that's degradation, separate system)
#
# Effects:
#   - Included in LLM prompts so agents can reason about their own wellbeing
#   - High wellbeing may make agents more exploratory / social (emergent, not coded)
#   - Wellbeing increase is an EVENT that can trigger an LLM call (reinforcement moment)
#
# The point: social behavior can emerge from ATTRACTION (seeking wellbeing)
# not just AVOIDANCE (fleeing degradation). This is the dual-drive system.

WELLBEING_MIN: float = 0.0
WELLBEING_MAX: float = 1.0
WELLBEING_INITIAL: float = 0.5  # new agents start with moderate wellbeing

# --- Curiosity / Novelty Drive ---
# Third motivation: agents are drawn to explore, discover, and create.
# Low curiosity narrows perception; high curiosity expands it.
CURIOSITY_MIN: float = 0.0
CURIOSITY_MAX: float = 1.0
CURIOSITY_INITIAL: float = 0.5


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------

@dataclass
class RelationshipRecord:
    """Tracks relationship between two agents."""
    interaction_count: int = 0
    positive_count: int = 0
    negative_count: int = 0
    last_interaction_tick: int = 0
    is_bonded: bool = False


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

class ActionType(str, Enum):
    MOVE = "move"
    GATHER = "gather"
    COMMUNICATE = "communicate"
    WAIT = "wait"
    SET_GOAL = "set_goal"           # agent sets a new goal
    UPDATE_PLAN = "update_plan"     # agent updates its multi-step plan
    DONE = "done"                   # agent ends its agentic turn
    BUILD = "build"                 # build a structure on current tile
    CONSUME = "consume"             # consume a resource from inventory to satisfy need
    STORE = "store"                 # deposit inventory resource into storage structure
    READ_MARKER = "read_marker"     # read message from a marker on current tile
    COMPOSE = "compose"             # combine existing structures into a higher-tier one
    PROPOSE_INNOVATION = "propose_innovation"  # propose an entirely new structure type
    PROPOSE_RULE = "propose_rule"   # propose a collective rule/norm
    ACCEPT_RULE = "accept_rule"     # accept a proposed collective rule
    IGNORE_RULE = "ignore_rule"     # explicitly decline a proposed rule
    GIVE = "give"                   # transfer a resource to a nearby agent
    REPAIR = "repair"               # repair a damaged structure on current tile


@dataclass
class Action:
    type: ActionType
    direction: Optional[tuple[int, int]] = None   # MOVE: (dx, dy), each in {-1, 0, 1}
    resource_type: Optional[str] = None            # GATHER: which resource
    message: Optional[str] = None                  # COMMUNICATE: free-form text
    target_agent_id: Optional[int] = None          # COMMUNICATE: who to address (-1 = broadcast)
    goal: Optional[str] = None                     # SET_GOAL: the goal text
    plan_steps: Optional[list[str]] = None         # UPDATE_PLAN: ordered plan steps
    structure_type: Optional[str] = None           # BUILD: which structure to build
    marker_message: Optional[str] = None           # BUILD marker: the message to write
    compose_targets: Optional[list[str]] = None    # COMPOSE: structure types to combine
    innovation_description: Optional[str] = None   # PROPOSE_INNOVATION: what the agent wants to create
    rule_text: Optional[str] = None                # PROPOSE_RULE: the rule content
    rule_id: Optional[int] = None                  # ACCEPT_RULE/IGNORE_RULE: which rule
    reasoning: str = ""                            # the agent's stated reason (from LLM)


# ---------------------------------------------------------------------------
# Events — triggers for LLM calls
# ---------------------------------------------------------------------------

class EventType(str, Enum):
    AGENT_ENTERED_PERCEPTION = "agent_entered_perception"
    AGENT_LEFT_PERCEPTION = "agent_left_perception"
    RESOURCE_DEPLETED = "resource_depleted"         # expected resource gone
    RESOURCE_DISCOVERED = "resource_discovered"     # new resource found
    NEEDS_CRITICAL = "needs_critical"               # a need dropped below threshold
    WELLBEING_INCREASED = "wellbeing_increased"     # reinforcement moment
    ENVIRONMENTAL_CHANGE = "environmental_change"   # world shift occurred
    REFLECTION = "reflection"                       # periodic self-assessment
    RECEIVED_MESSAGE = "received_message"           # another agent communicated
    PLAN_STEP_DUE = "plan_step_due"                 # next step in plan is ready to execute
    STRUCTURE_DISCOVERED = "structure_discovered"   # agent perceives a structure for first time
    COMPOSITION_ATTEMPTED = "composition_attempted" # agent tried to compose structures
    INNOVATION_PROPOSED = "innovation_proposed"     # agent proposed a new structure type
    RULE_PROPOSED = "rule_proposed"                 # agent proposed a collective rule
    SPECIALISATION_GAINED = "specialisation_gained" # agent reached specialisation threshold


@dataclass
class Event:
    type: EventType
    tick: int
    agent_id: int
    data: dict = field(default_factory=dict)

    def summary(self) -> str:
        """Human-readable one-liner for logs."""
        return f"[Tick {self.tick}] Agent {self.agent_id}: {self.type.value} — {self.data}"


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

@dataclass
class MemoryEntry:
    tick: int
    summary: str
    importance: float = 0.5     # higher = retained longer during eviction
    access_count: int = 0       # incremented each time included in LLM prompt


# ---------------------------------------------------------------------------
# Communication
# ---------------------------------------------------------------------------

@dataclass
class Message:
    sender_id: int
    receiver_id: int    # -1 = broadcast to all agents in communication range
    content: str
    tick: int


# ---------------------------------------------------------------------------
# Agent State — the full contract
# ---------------------------------------------------------------------------
#
# This is the single source of truth for an agent's state.
# The engine reads/writes needs, wellbeing, capabilities each tick.
# The runtime reads everything for perception, decisions, memory.
# Persistence serialises and deserialises this entire object.

@dataclass
class AgentState:
    id: int
    position: Position
    needs: NeedsState
    wellbeing: float                # [0.0, 1.0], see Wellbeing section above
    capabilities: Capabilities
    curiosity: float = 0.5              # [0.0, 1.0], novelty/exploration drive
    memories: list[MemoryEntry] = field(default_factory=list)
    age: int = 0                    # ticks alive
    alive_since_tick: int = 0       # world tick when this agent was created
    current_action: Optional[Action] = None     # what they're doing right now

    # --- Agentic state: goals and plans persist across turns ---
    goals: list[str] = field(default_factory=list)      # active goals, set by the agent itself
    plan: list[str] = field(default_factory=list)        # ordered plan steps toward current goal
    current_routine: Optional[str] = None                # deterministic routine label between turns

    # Inventory: resources the agent is carrying (max agent_carry_capacity)
    inventory: list[str] = field(default_factory=list)

    # Tracking for wellbeing bonuses — which agents interacted with this tick
    interactions_this_tick: list[int] = field(default_factory=list)

    # Set of agent IDs currently visible (for detecting enter/leave perception events)
    agents_in_perception: set[int] = field(default_factory=set)

    # Set of known resource locations (for detecting depletion events)
    known_resources: dict[tuple[int, int], str] = field(default_factory=dict)

    # --- Practice-based specialisation ---
    # Tracks cumulative activity counts: {"gather": 15, "build": 8, "communicate": 22}
    activity_counts: dict[str, int] = field(default_factory=dict)
    # Activities where the agent has crossed the specialisation threshold
    specialisations: list[str] = field(default_factory=list)

    # --- Composition knowledge ---
    # Recipe names this agent has discovered or learned about
    known_recipes: list[str] = field(default_factory=list)

    # --- Curiosity tracking ---
    visited_tiles: set[tuple[int, int]] = field(default_factory=set)
    met_agents: set[int] = field(default_factory=set)

    # --- Relationship tracking ---
    relationships: dict[int, "RelationshipRecord"] = field(default_factory=dict)

    # --- Maslow drive tracking ---
    ticks_survival_stable: int = 0          # consecutive ticks all survival needs > 0.4
    structures_built_count: int = 0         # structures this agent has built
    innovations_proposed: list[str] = field(default_factory=list)  # innovation names proposed
    rules_established_count: int = 0        # rules this agent proposed that became established
    recent_actions: list[str] = field(default_factory=list)  # action types from recent ticks
    maslow_level: int = 1                   # highest active Maslow level (1-8)


# ---------------------------------------------------------------------------
# World State — snapshot for persistence and watcher
# ---------------------------------------------------------------------------

@dataclass
class WorldState:
    tick: int
    grid_width: int
    grid_height: int
    tiles: list[list[Tile]]             # tiles[x][y]
    agents: dict[int, AgentState]       # agent_id -> AgentState
    next_agent_id: int                  # counter for assigning IDs to new arrivals
    messages_this_tick: list[Message] = field(default_factory=list)
    events_this_tick: list[Event] = field(default_factory=list)
    event_log: list[Event] = field(default_factory=list)
    message_log: list[Message] = field(default_factory=list)

    # --- Composition registry ---
    discovered_recipes: list[DiscoveredRecipe] = field(default_factory=list)

    # --- Collective rules ---
    collective_rules: list[CollectiveRule] = field(default_factory=list)
    next_rule_id: int = 0  # counter for assigning rule IDs


# ---------------------------------------------------------------------------
# Event Bus — streaming layer for all simulation events
# ---------------------------------------------------------------------------
#
# The EventBus is the single source of truth for everything that happens.
# Every meaningful event — agent reasoning, actions, conversations, goal
# changes, watcher observations — flows through the bus.
#
# Consumers:
#   - CLI output (sync subscriber, prints formatted events)
#   - Persistent event log (sync subscriber, appends to JSONL)
#   - WebSocket feed (async subscriber, pushes to connected frontends)
#
# The bus decouples event production (agentic loop, tick engine) from
# event consumption (display, logging, streaming).

class BusEventType(str, Enum):
    # --- Agentic loop events ---
    AGENTIC_TURN_START = "agentic_turn_start"
    REASONING_STEP = "reasoning_step"         # agent thought/reasoned (includes LLM response)
    ACTION_TAKEN = "action_taken"             # agent executed an action within the loop
    OBSERVATION = "observation"               # agent perceived result of action
    GOAL_SET = "goal_set"                     # agent set or changed a goal
    GOAL_COMPLETED = "goal_completed"         # agent marked a goal as done
    PLAN_UPDATED = "plan_updated"             # agent changed its plan
    AGENTIC_TURN_END = "agentic_turn_end"

    # --- Communication ---
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"

    # --- World events ---
    AGENT_ARRIVED = "agent_arrived"
    AGENT_MOVED = "agent_moved"
    AGENT_GATHERED = "agent_gathered"
    ENVIRONMENTAL_SHIFT = "environmental_shift"

    # --- Status changes ---
    DEGRADATION_CHANGED = "degradation_changed"
    WELLBEING_CHANGED = "wellbeing_changed"
    NEEDS_CRITICAL = "needs_critical"

    # --- Building / structures ---
    STRUCTURE_BUILT = "structure_built"
    STRUCTURE_DECAYED = "structure_decayed"
    STRUCTURE_DISCOVERED = "structure_discovered"
    RESOURCE_STORED = "resource_stored"
    RESOURCE_CONSUMED = "resource_consumed"
    MARKER_READ = "marker_read"

    # --- Composition & innovation ---
    COMPOSITION_DISCOVERED = "composition_discovered"   # new recipe found via composition
    COMPOSITION_FAILED = "composition_failed"           # composition attempt produced nothing
    INNOVATION_SUCCEEDED = "innovation_succeeded"       # LLM approved an innovation proposal
    INNOVATION_FAILED = "innovation_failed"             # LLM rejected an innovation proposal

    # --- Collective rules ---
    RULE_PROPOSED = "rule_proposed"
    RULE_ACCEPTED = "rule_accepted"
    RULE_ESTABLISHED = "rule_established"               # adoption crossed threshold

    # --- Resource transfer ---
    RESOURCE_GIVEN = "resource_given"

    # --- Repair ---
    STRUCTURE_REPAIRED = "structure_repaired"

    # --- Specialisation ---
    SPECIALISATION_GAINED = "specialisation_gained"

    # --- Feedback loops ---
    MAINTENANCE_CONSUMED = "maintenance_consumed"       # structure consumed maintenance resources
    CROWDING_EFFECT = "crowding_effect"                 # crowding depletion applied

    # --- Deterministic behavior ---
    DETERMINISTIC_ACTION = "deterministic_action"

    # --- Tick-level ---
    TICK_START = "tick_start"
    TICK_END = "tick_end"

    # --- Watcher (Phase 2) ---
    WATCHER_TICK_REPORT = "watcher_tick_report"
    WATCHER_NARRATIVE = "watcher_narrative"
    WATCHER_MILESTONE = "watcher_milestone"


@dataclass
class BusEvent:
    """A rich event emitted to the event bus.

    Every meaningful thing that happens in the simulation becomes a BusEvent.
    These are the atoms of the live feed and the persistent event log.
    """
    type: BusEventType
    tick: int
    timestamp: float = field(default_factory=time.time)  # wall-clock for ordering
    agent_id: Optional[int] = None      # None for world/tick events
    data: dict = field(default_factory=dict)

    def summary(self) -> str:
        agent_str = f"Agent {self.agent_id}" if self.agent_id is not None else "World"
        return f"[Tick {self.tick}] {agent_str}: {self.type.value}"


class EventBus:
    """Central event bus for streaming simulation events.

    Sync and async subscribers receive events in emit order.
    The bus also maintains a complete log for retrospective queries.
    """

    def __init__(self) -> None:
        self._sync_subscribers: list[Callable[[BusEvent], None]] = []
        self._async_subscribers: list[Callable[[BusEvent], Awaitable[None]]] = []
        self._log: list[BusEvent] = []

    def subscribe(self, callback: Callable[[BusEvent], None]) -> None:
        """Register a synchronous subscriber."""
        self._sync_subscribers.append(callback)

    def subscribe_async(self, callback: Callable[[BusEvent], Awaitable[None]]) -> None:
        """Register an async subscriber (e.g. WebSocket push)."""
        self._async_subscribers.append(callback)

    async def emit(self, event: BusEvent) -> None:
        """Emit an event to all subscribers and append to the log."""
        self._log.append(event)
        for sub in self._sync_subscribers:
            sub(event)
        for sub in self._async_subscribers:
            await sub(event)

    def emit_sync(self, event: BusEvent) -> None:
        """Emit synchronously (for use outside async context). Skips async subscribers."""
        self._log.append(event)
        for sub in self._sync_subscribers:
            sub(event)

    def get_log(self, since_tick: int = 0) -> list[BusEvent]:
        """Return all events from *since_tick* onward."""
        return [e for e in self._log if e.tick >= since_tick]

    def get_log_by_agent(self, agent_id: int, since_tick: int = 0) -> list[BusEvent]:
        """Return events for a specific agent."""
        return [e for e in self._log if e.agent_id == agent_id and e.tick >= since_tick]

    def get_log_by_type(self, event_type: BusEventType, since_tick: int = 0) -> list[BusEvent]:
        """Return events of a specific type."""
        return [e for e in self._log if e.type == event_type and e.tick >= since_tick]
