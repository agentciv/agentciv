"""Agent class for Agent Civilisation.

Wraps AgentState and provides the high-level methods the tick loop calls.
All types are imported from src.types — nothing is redefined here.
"""

from __future__ import annotations

from typing import Optional

from src.config import SimulationConfig
from src.types import (
    AgentState,
    Capabilities,
    MemoryEntry,
    NeedsState,
    Position,
    CURIOSITY_INITIAL,
    WELLBEING_INITIAL,
    WELLBEING_MAX,
    WELLBEING_MIN,
)
from src.agents.memory import MemoryStore


# Maximum active goals per agent — prevents unbounded accumulation.
_MAX_GOALS = 5


class Agent:
    """High-level wrapper around AgentState.

    Owns the state and exposes methods for the tick loop (needs depletion,
    capability degradation/recovery, wellbeing, memory, resource gathering)
    and for the agentic loop (goals, plans).
    """

    def __init__(
        self,
        config: SimulationConfig,
        agent_id: int,
        position: Position,
        alive_since_tick: int,
    ) -> None:
        self.config = config

        self.state = AgentState(
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
            alive_since_tick=alive_since_tick,
            goals=[],
            plan=[],
        )

        # Memory store wraps the list living inside AgentState
        self.memory_store = MemoryStore(
            self.state.memories, self.state.capabilities.base_memory_capacity
        )

    # ------------------------------------------------------------------
    # Needs
    # ------------------------------------------------------------------

    def update_needs(self, rate: float) -> None:
        """Deplete all needs by *rate* (clamped to 0.0)."""
        self.state.needs.deplete_all(rate)

    # ------------------------------------------------------------------
    # Capability degradation / recovery
    # ------------------------------------------------------------------

    def apply_degradation(self, rate: float) -> None:
        """Degrade capabilities when ANY need is below DEGRADATION_THRESHOLD.

        Each capability moves toward its minimum:
            new_val = current - (current - minimum) * rate
        Then clamped to [minimum, base].
        """
        caps = self.state.capabilities
        if not self.state.needs.any_critical(Capabilities.DEGRADATION_THRESHOLD):
            return

        caps.perception_range = max(
            caps.MIN_PERCEPTION_RANGE,
            caps.perception_range - (caps.perception_range - caps.MIN_PERCEPTION_RANGE) * rate,
        )
        caps.movement_speed = max(
            caps.MIN_MOVEMENT_SPEED,
            caps.movement_speed - (caps.movement_speed - caps.MIN_MOVEMENT_SPEED) * rate,
        )
        new_mem = int(
            caps.memory_capacity
            - (caps.memory_capacity - caps.MIN_MEMORY_CAPACITY) * rate
        )
        caps.memory_capacity = max(caps.MIN_MEMORY_CAPACITY, new_mem)

        # Keep memory store capacity in sync
        self.memory_store.capacity = caps.memory_capacity

    def apply_recovery(self, rate: float) -> None:
        """Recover capabilities when ALL needs are above RECOVERY_THRESHOLD.

        Each capability moves toward its base:
            new_val = current + (base - current) * rate
        Then clamped to [minimum, base].
        """
        caps = self.state.capabilities
        if not self.state.needs.all_healthy(Capabilities.RECOVERY_THRESHOLD):
            return

        caps.perception_range = min(
            caps.base_perception_range,
            caps.perception_range + (caps.base_perception_range - caps.perception_range) * rate,
        )
        caps.movement_speed = min(
            caps.base_movement_speed,
            caps.movement_speed + (caps.base_movement_speed - caps.movement_speed) * rate,
        )
        new_mem = int(
            caps.memory_capacity
            + (caps.base_memory_capacity - caps.memory_capacity) * rate
        )
        caps.memory_capacity = min(caps.base_memory_capacity, max(caps.memory_capacity, new_mem))

        # Keep memory store capacity in sync
        self.memory_store.capacity = caps.memory_capacity

    # ------------------------------------------------------------------
    # Wellbeing
    # ------------------------------------------------------------------

    def update_wellbeing_decay(self, rate: float) -> None:
        """Natural wellbeing decay per tick."""
        self.state.wellbeing = max(
            WELLBEING_MIN, self.state.wellbeing - rate
        )

    def add_wellbeing_bonus(self, amount: float) -> None:
        """Increase wellbeing from a positive interaction."""
        self.state.wellbeing = min(
            WELLBEING_MAX, self.state.wellbeing + amount
        )

    # ------------------------------------------------------------------
    # Resource gathering
    # ------------------------------------------------------------------

    def gather_resource(self, resource_type: str, restore_amount: float) -> None:
        """Satisfy a need by gathering a resource."""
        self.state.needs.satisfy(resource_type, restore_amount)

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def add_memory(self, entry: MemoryEntry) -> None:
        """Add a memory entry, evicting if at capacity."""
        self.memory_store.add(entry)

    def get_memory_summary(self, max_entries: int = 20) -> str:
        """Return a compressed text summary of memories for LLM prompts."""
        return self.memory_store.get_summary(max_entries)

    # ------------------------------------------------------------------
    # Goals
    # ------------------------------------------------------------------

    def set_goal(self, goal: str) -> None:
        """Add a goal to the agent's active goals list.

        Caps at _MAX_GOALS goals — if at capacity, the oldest goal is
        removed to make room (assumption: oldest is least relevant).
        """
        goal = goal.strip()
        if not goal:
            return
        # Avoid duplicates
        if goal in self.state.goals:
            return
        # Evict oldest if at capacity
        while len(self.state.goals) >= _MAX_GOALS:
            self.state.goals.pop(0)
        self.state.goals.append(goal)

    def complete_goal(self, goal: str) -> None:
        """Remove a completed goal from the active goals list."""
        goal = goal.strip()
        if goal in self.state.goals:
            self.state.goals.remove(goal)

    def get_goals_summary(self) -> str:
        """Format goals for inclusion in LLM prompts."""
        if not self.state.goals:
            return "none yet"
        return ", ".join(f"{i + 1}. {g}" for i, g in enumerate(self.state.goals))

    # ------------------------------------------------------------------
    # Plan
    # ------------------------------------------------------------------

    def update_plan(self, steps: list[str]) -> None:
        """Replace the agent's plan with new ordered steps."""
        self.state.plan = [s.strip() for s in steps if s.strip()]

    def advance_plan(self) -> Optional[str]:
        """Pop and return the first step of the plan.

        Returns None if the plan is empty. Used by deterministic_action
        to execute plan steps without an LLM call.
        """
        if not self.state.plan:
            return None
        return self.state.plan.pop(0)

    def has_plan(self) -> bool:
        """Whether the agent has remaining plan steps."""
        return len(self.state.plan) > 0

    def get_plan_summary(self) -> str:
        """Format plan steps for inclusion in LLM prompts."""
        if not self.state.plan:
            return "none yet"
        lines = []
        for i, step in enumerate(self.state.plan):
            marker = ">>>" if i == 0 else "   "
            lines.append(f"{marker} {i + 1}. {step}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Status queries
    # ------------------------------------------------------------------

    def is_degraded(self) -> bool:
        """Whether any capability is currently below its base value."""
        caps = self.state.capabilities
        return (
            caps.perception_range < caps.base_perception_range
            or caps.movement_speed < caps.base_movement_speed
            or caps.memory_capacity < caps.base_memory_capacity
        )

    # ------------------------------------------------------------------
    # Tick housekeeping
    # ------------------------------------------------------------------

    def clear_tick_state(self) -> None:
        """Reset per-tick tracking fields at the start of a new tick."""
        self.state.interactions_this_tick.clear()
        self.state.current_action = None
        self.state.age += 1
