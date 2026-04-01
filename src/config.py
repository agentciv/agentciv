"""Configuration loader for Agent Civilisation.

Reads a YAML config file and exposes all parameters as a typed dataclass.
Every simulation parameter is configurable — this is what makes every fork
a unique experiment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SimulationConfig:
    """All simulation parameters. Loaded from YAML, with sane defaults."""

    # -- World ---------------------------------------------------------------
    grid_width: int = 50
    grid_height: int = 50
    resource_types: list[str] = field(
        default_factory=lambda: ["water", "food", "material"]
    )
    resource_distribution: str = "clustered"  # clustered | scattered | banded | random
    resource_depletion_rate: float = 0.1      # amount removed per gather action
    resource_regeneration_rate: float = 0.05  # amount restored per tick
    resource_cluster_count: int = 3           # clusters per resource type (if clustered)
    resource_cluster_radius: int = 5          # radius of each cluster
    resource_max_per_tile: float = 1.0        # max resource amount on a single tile

    terrain_types: list[str] = field(
        default_factory=lambda: ["plain", "rocky", "dense"]
    )
    movement_cost: dict[str, int] = field(
        default_factory=lambda: {"plain": 1, "rocky": 2, "dense": 3}
    )

    # -- Agents --------------------------------------------------------------
    initial_agent_count: int = 50
    agent_perception_range: int = 3           # base tiles visible in each direction
    agent_communication_range: int = 2        # max distance for messaging
    agent_base_movement_speed: float = 1.0    # base tiles per tick on plain terrain

    # Needs
    agent_needs_depletion_rate: float = 0.02  # per tick, per need
    agent_gather_restore: float = 0.3         # need restored per successful gather

    # Degradation / recovery
    agent_degradation_rate: float = 0.01      # rate capabilities shrink when needs unmet
    agent_recovery_rate: float = 0.02         # rate capabilities restore when needs met

    # Wellbeing
    agent_wellbeing_interaction_bonus: float = 0.05  # per positive interaction
    agent_wellbeing_decay_rate: float = 0.005        # natural decay per tick
    agent_wellbeing_proximity_bonus: float = 0.01    # small bonus for being near others

    # Curiosity / Novelty drive
    agent_curiosity_decay_rate: float = 0.003         # natural decay per tick (slower than wellbeing)
    agent_curiosity_exploration_bonus: float = 0.03   # visiting a new tile
    agent_curiosity_discovery_bonus: float = 0.04     # building, composing, or innovating
    agent_curiosity_social_bonus: float = 0.02        # meeting a new agent
    agent_curiosity_learning_bonus: float = 0.01      # receiving new info via conversation

    # Relationships / Bonds
    agent_bond_threshold: int = 10           # positive interactions needed to form a bond
    agent_bond_social_multiplier: float = 2.0  # bonded agents recover social wellbeing 2x from each other

    # Memory
    agent_memory_capacity: int = 100
    agent_memory_decay: bool = False          # if True, oldest memories lose importance

    # Reflection
    agent_reflection_interval: int = 25       # ticks between periodic LLM reflection calls

    # -- Population dynamics -------------------------------------------------
    new_agent_interval: int = 50              # ticks between new arrivals
    new_agent_spawn: str = "random"           # random | edge | centre

    # -- Environmental shifts ------------------------------------------------
    enable_environmental_shifts: bool = True
    shift_interval: int = 500                 # ticks between shifts
    shift_severity: str = "moderate"          # mild | moderate | severe

    # -- Building / structures ------------------------------------------------
    agent_carry_capacity: int = 3             # max resources an agent can hold at once
    structures: dict = field(default_factory=lambda: {
        "shelter": {
            "requires": ["water", "material"],
            "effect": "reduce_degradation",
            "effect_strength": 0.5,
            "decay_rate": 0.001,
        },
        "storage": {
            "requires": ["food", "material"],
            "effect": "store_resources",
            "capacity": 10,
            "decay_rate": 0.001,
        },
        "marker": {
            "requires": ["material"],
            "effect": "persistent_message",
            "decay_rate": 0.002,
        },
        "path": {
            "requires": ["material", "material"],
            "effect": "reduce_movement_cost",
            "effect_strength": 0.5,
            "decay_rate": 0.0005,
        },
    })

    # -- Feedback loops -------------------------------------------------------
    enable_environmental_coevolution: bool = True   # world changes in response to agent activity
    heavy_gathering_regen_penalty: float = 0.5      # multiplier on regen when gathering_pressure is high
    crowding_depletion_multiplier: float = 1.5      # gather depletes faster when many agents on tile
    structure_maintenance_cost: float = 0.01        # resources consumed per structure per tick
    # Positive feedback: structures boost resource regeneration on their tile
    structure_regen_bonus: float = 0.15             # per healthy structure, multiplicative on regen rate

    # -- Settlement detection --------------------------------------------------
    settlement_structure_threshold: int = 4         # structures within range to count as settlement
    settlement_range: int = 2                       # Chebyshev distance for settlement detection
    settlement_need_depletion_reduction: float = 0.15  # 15% slower need depletion in settlements
    settlement_wellbeing_bonus: float = 0.01        # per-tick wellbeing bonus for settlement residents

    # -- Repair ----------------------------------------------------------------
    repair_health_restore: float = 1.0              # health restored per repair action (to max 1.0)

    # -- Innovation & composition ----------------------------------------------
    enable_innovation: bool = True                  # agents can propose novel structures
    enable_composition: bool = True                 # agents can combine structures
    innovation_evaluation_model: str = ""           # separate model for innovation eval (empty = use main)

    # -- Specialisation --------------------------------------------------------
    enable_specialisation: bool = True
    specialisation_threshold: int = 20              # activity repetitions before bonus kicks in (legacy, used if tiers absent)
    specialisation_bonus: float = 0.1               # efficiency multiplier per specialisation level (legacy)
    # Tiered specialisation: agents progress through levels of mastery
    specialisation_tiers: dict = field(default_factory=lambda: {
        "novice": {"threshold": 10, "bonus": 0.05},
        "skilled": {"threshold": 20, "bonus": 0.15},
        "expert": {"threshold": 40, "bonus": 0.30},
        "master": {"threshold": 60, "bonus": 0.50},
    })

    # -- Collective rules ------------------------------------------------------
    enable_collective_rules: bool = True
    rule_establishment_threshold: float = 0.6       # adoption rate needed for a rule to become established
    # Mechanical effects: established rules reduce need depletion for all agents
    rule_need_depletion_reduction: float = 0.02     # per established rule, max reduced by max_active_rules * this
    max_active_rules: int = 5                       # cap on how many rules provide mechanical benefit

    # -- Simulation ----------------------------------------------------------
    ticks_per_real_minute: float = 0          # 0 = fast mode (no clock, advance ASAP)
    max_interactions_per_tick: int = 3        # cap multi-turn exchanges per agent pair
    max_concurrent_llm_calls: int = 10        # parallelism cap for LLM calls within a tick
    max_steps_per_agentic_turn: int = 4       # ReAct loop steps per agent turn

    # -- LLM -----------------------------------------------------------------
    model_provider: str = "openai"            # openai | anthropic | google | local
    model_name: str = "gpt-4o-mini"
    api_key_env_var: str = "AGENT_CIV_API_KEY"
    llm_max_tokens: int = 300                 # max response tokens per agent call
    llm_temperature: float = 0.7

    # -- Watcher (Phase 2, included here for completeness) -------------------
    narrative_report_interval: int = 50
    enable_milestone_reports: bool = True

    # -- Persistence ---------------------------------------------------------
    save_interval: int = 10                   # ticks between state saves
    save_path: str = "./data/simulation_state"
    log_path: str = "./data/logs"

    # -- CLI -----------------------------------------------------------------
    log_level: str = "INFO"                   # DEBUG | INFO | WARNING
    show_agent_reasoning: bool = True         # print LLM reasoning to terminal
    show_conversations: bool = True           # print agent conversations to terminal

    @classmethod
    def from_yaml(cls, path: str | Path) -> SimulationConfig:
        """Load config from a YAML file, falling back to defaults for missing keys."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        # Only pass keys that match dataclass fields
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in raw.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def default(cls) -> SimulationConfig:
        """Return default config (the fishbowl config)."""
        return cls()
