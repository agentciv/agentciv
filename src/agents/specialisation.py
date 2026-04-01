"""Practice-based specialisation for Agent Civilisation.

Tracks cumulative activity counts per agent and awards specialisation
bonuses when thresholds are crossed. Specialisation is EMERGENT — agents
aren't assigned roles; they develop efficiency through repetition.

TIERED SYSTEM (v2):
  - Novice (10 actions): +5% bonus — first glimmer of skill
  - Skilled (20 actions): +15% bonus — reliably better than average
  - Expert (40 actions): +30% bonus — recognised specialist
  - Master (60 actions): +50% bonus — can TEACH others via communication

Agents can have multiple specialisations at different tiers. A master
builder who is only a novice gatherer creates genuine interdependence —
they NEED other agents to gather efficiently while they build.
"""

from __future__ import annotations

import logging

from src.config import SimulationConfig
from src.types import AgentState

logger = logging.getLogger("agent_civilisation.specialisation")


# Map action type values to their specialisation activity name.
# Only physical actions that benefit from practice are included.
_ACTION_TO_ACTIVITY: dict[str, str] = {
    "move": "movement",
    "gather": "gathering",
    "build": "building",
    "communicate": "communication",
    "compose": "composition",
    "store": "storage",
    "repair": "building",  # repair counts toward building skill
}

# Ordered from highest to lowest for tier lookup
_TIER_ORDER = ["master", "expert", "skilled", "novice"]


def _get_tier(count: int, config: SimulationConfig) -> tuple[str | None, float]:
    """Return (tier_name, bonus) for the given activity count.

    Uses config.specialisation_tiers if available, falls back to legacy
    single-threshold system for backward compatibility.
    """
    tiers = getattr(config, "specialisation_tiers", None)
    if not tiers:
        # Legacy: single threshold
        if count >= config.specialisation_threshold:
            return "specialised", config.specialisation_bonus
        return None, 0.0

    # Tiered: find the highest tier reached
    best_tier = None
    best_bonus = 0.0
    for tier_name in _TIER_ORDER:
        tier_info = tiers.get(tier_name)
        if tier_info and count >= tier_info["threshold"]:
            if tier_info["bonus"] > best_bonus:
                best_tier = tier_name
                best_bonus = tier_info["bonus"]
    return best_tier, best_bonus


def record_activity(agent: AgentState, action_type: str, config: SimulationConfig) -> str | None:
    """Record an activity and check for new specialisation or tier upgrade.

    Returns the activity name if a NEW specialisation was gained, else None.
    """
    if not config.enable_specialisation:
        return None

    activity = _ACTION_TO_ACTIVITY.get(action_type)
    if activity is None:
        return None

    # Increment count
    agent.activity_counts[activity] = agent.activity_counts.get(activity, 0) + 1
    count = agent.activity_counts[activity]

    # Check for tier crossing (any tier threshold)
    tiers = getattr(config, "specialisation_tiers", None)
    if tiers:
        for tier_info in tiers.values():
            if count == tier_info["threshold"]:
                if activity not in agent.specialisations:
                    agent.specialisations.append(activity)
                    logger.info(
                        "Agent %d gained specialisation in %s (%d repetitions)",
                        agent.id, activity, count,
                    )
                    return activity
                else:
                    # Already specialised — tier upgrade (logged but not returned as "new")
                    tier_name, bonus = _get_tier(count, config)
                    logger.info(
                        "Agent %d advanced to %s tier in %s (%d repetitions, +%.0f%% bonus)",
                        agent.id, tier_name, activity, count, bonus * 100,
                    )
                    return activity  # return so bus event fires for tier upgrades too
    else:
        # Legacy single threshold
        if count == config.specialisation_threshold and activity not in agent.specialisations:
            agent.specialisations.append(activity)
            logger.info(
                "Agent %d gained specialisation in %s (%d repetitions)",
                agent.id, activity, count,
            )
            return activity

    return None


def get_efficiency_bonus(agent: AgentState, action_type: str, config: SimulationConfig) -> float:
    """Return the efficiency multiplier for an agent performing an action.

    Uses tiered bonuses: novice +5%, skilled +15%, expert +30%, master +50%.
    Returns 1.0 (no bonus) if the agent has no relevant specialisation.
    """
    if not config.enable_specialisation:
        return 1.0

    activity = _ACTION_TO_ACTIVITY.get(action_type)
    if activity is None:
        return 1.0

    count = agent.activity_counts.get(activity, 0)
    _, bonus = _get_tier(count, config)
    if bonus > 0:
        return 1.0 + bonus

    return 1.0


def get_tier_name(agent: AgentState, activity: str, config: SimulationConfig) -> str:
    """Return the tier name for an agent's specialisation in an activity."""
    count = agent.activity_counts.get(activity, 0)
    tier_name, _ = _get_tier(count, config)
    return tier_name or "untrained"


def is_master(agent: AgentState, activity: str, config: SimulationConfig) -> bool:
    """Check if agent has master tier in an activity (can teach)."""
    tiers = getattr(config, "specialisation_tiers", None)
    if not tiers or "master" not in tiers:
        return False
    count = agent.activity_counts.get(activity, 0)
    return count >= tiers["master"]["threshold"]


def apply_teaching(
    teacher: AgentState,
    learner: AgentState,
    config: SimulationConfig,
) -> str | None:
    """When a master communicates with another agent, transfer skill XP.

    The learner gains +3 actions toward each of the teacher's master-tier
    specialisations. Returns a description of what was taught, or None.
    """
    tiers = getattr(config, "specialisation_tiers", None)
    if not tiers or "master" not in tiers:
        return None

    master_threshold = tiers["master"]["threshold"]
    taught: list[str] = []

    for activity in teacher.specialisations:
        teacher_count = teacher.activity_counts.get(activity, 0)
        if teacher_count >= master_threshold:
            # Teacher is a master in this activity — grant XP to learner
            learner_count = learner.activity_counts.get(activity, 0)
            if learner_count < teacher_count:  # can only learn from someone better
                learner.activity_counts[activity] = learner.activity_counts.get(activity, 0) + 3
                taught.append(activity)

                # Check if learner crossed a tier threshold
                new_count = learner.activity_counts[activity]
                for tier_info in tiers.values():
                    if learner_count < tier_info["threshold"] <= new_count:
                        if activity not in learner.specialisations:
                            learner.specialisations.append(activity)
                            logger.info(
                                "Agent %d learned %s from Agent %d (now at %d)",
                                learner.id, activity, teacher.id, new_count,
                            )

    if taught:
        return f"taught {', '.join(taught)}"
    return None


def describe_specialisations(agent: AgentState, config: SimulationConfig | None = None) -> str:
    """Return a human-readable description of agent's specialisations for LLM prompt."""
    if not agent.specialisations:
        return "none"

    parts: list[str] = []
    for spec in agent.specialisations:
        count = agent.activity_counts.get(spec, 0)
        if config:
            tier = get_tier_name(agent, spec, config)
            parts.append(f"{spec} [{tier}] ({count} actions)")
        else:
            parts.append(f"{spec} ({count} actions)")
    return ", ".join(parts)


def describe_activity_progress(agent: AgentState, config: SimulationConfig) -> str:
    """Show activity counts relative to next specialisation tier.

    Only includes activities that have been performed at least once.
    """
    if not agent.activity_counts:
        return "no significant activity patterns yet"

    tiers = getattr(config, "specialisation_tiers", None)
    parts: list[str] = []

    for activity, count in sorted(agent.activity_counts.items(), key=lambda x: -x[1]):
        if tiers:
            current_tier, _ = _get_tier(count, config)
            # Find next tier threshold
            next_threshold = None
            for tier_name in ["novice", "skilled", "expert", "master"]:
                tier_info = tiers.get(tier_name)
                if tier_info and tier_info["threshold"] > count:
                    next_threshold = tier_info["threshold"]
                    next_tier_name = tier_name
                    break

            if current_tier == "master":
                parts.append(f"{activity}: master ({count})")
            elif current_tier:
                pct = min(100, int(count / next_threshold * 100)) if next_threshold else 100
                parts.append(f"{activity}: {current_tier} ({count}, next: {next_tier_name} at {next_threshold})")
            else:
                first_threshold = tiers.get("novice", {}).get("threshold", 10)
                pct = min(100, int(count / first_threshold * 100))
                parts.append(f"{activity}: {count}/{first_threshold} ({pct}%)")
        else:
            # Legacy
            threshold = config.specialisation_threshold
            if activity in agent.specialisations:
                parts.append(f"{activity}: specialised ({count})")
            else:
                pct = min(100, int(count / threshold * 100))
                parts.append(f"{activity}: {count}/{threshold} ({pct}%)")

    return ", ".join(parts)
