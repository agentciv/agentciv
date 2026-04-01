"""Maslow hierarchy of intrinsic drives for Agent Civilisation.

Agents have 8 levels of drives that unlock progressively as lower
needs are met. Higher drives are presented as FELT STATES — descriptive
text in the agent prompt, not numbers. The agent decides what to do
about each feeling. This is how civilisation emerges without prescription.

Levels:
  1. Survival          — water, food, material (always active)
  2. Safety/Planning   — future anxiety, reserves, stability
  3. Social Belonging  — group identity, loneliness, shared purpose
  4. Esteem            — achievement, recognition, status
  5. Cognitive         — curiosity, understanding, teaching
  6. Creative          — building, innovating, composing
  7. Self-Actualisation — purpose, meaning, legacy
  8. Transcendence     — collective purpose, mentoring, leaving something for others
"""

from __future__ import annotations

from src.types import AgentState, Capabilities
from src.config import SimulationConfig


# ---------------------------------------------------------------------------
# Maslow level computation
# ---------------------------------------------------------------------------

def compute_maslow_level(agent: AgentState, config: SimulationConfig) -> int:
    """Determine the highest active Maslow level (1-8).

    Each level requires the previous level to be met. The thresholds
    are deliberately lenient — the point is to make drives FELT, not
    to create a grind.
    """
    # Level 1: Always active
    level = 1

    # Level 2: Safety — survival stable for 2+ ticks
    if agent.ticks_survival_stable < 2:
        return level
    level = 2

    # Level 3: Social — wellbeing above 0.3 (some social contact)
    if agent.wellbeing < 0.3:
        return level
    level = 3

    # Level 4: Esteem — at least 2 relationships formed
    if len(agent.relationships) < 2:
        return level
    level = 4

    # Level 5: Cognitive — curiosity above 0.2 (some exploration done)
    if agent.curiosity < 0.2:
        return level
    level = 5

    # Level 6: Creative — visited 8+ unique tiles (knows the world enough to shape it)
    if len(agent.visited_tiles) < 8:
        return level
    level = 6

    # Level 7: Self-actualisation — built at least 1 structure
    if agent.structures_built_count < 1:
        return level
    level = 7

    # Level 8: Transcendence — proposed an innovation or established a rule
    if not agent.innovations_proposed and agent.rules_established_count < 1:
        return level
    level = 8

    return level


# ---------------------------------------------------------------------------
# Wellbeing ceiling — agents can't reach max wellbeing without higher drives
# ---------------------------------------------------------------------------

# Maps maslow level to the maximum wellbeing achievable at that level.
# This is the mechanic that breaks the 0.93 plateau.
MASLOW_WELLBEING_CEILING = {
    1: 0.45,   # Survival only — you're alive but unfulfilled
    2: 0.55,   # Safety met — a bit more settled
    3: 0.65,   # Social belonging — connected but not accomplished
    4: 0.75,   # Esteem — recognised but haven't created
    5: 0.80,   # Cognitive — curious and exploring
    6: 0.88,   # Creative — actively building and shaping the world
    7: 0.95,   # Self-actualised — purposeful
    8: 1.00,   # Transcendence — full flourishing
}


def apply_wellbeing_ceiling(agent: AgentState) -> None:
    """Hard-cap wellbeing at the Maslow ceiling for the agent's current level.

    This is the core mechanic that prevents the contentment plateau.
    Without higher drives satisfied, wellbeing simply cannot exceed
    the ceiling — creating genuine restlessness and motivation.
    """
    ceiling = MASLOW_WELLBEING_CEILING.get(agent.maslow_level, 1.0)
    if agent.wellbeing > ceiling:
        agent.wellbeing = ceiling


# ---------------------------------------------------------------------------
# Survival stability tracking
# ---------------------------------------------------------------------------

def update_survival_stability(agent: AgentState) -> None:
    """Update consecutive ticks of survival stability.

    Called once per tick. Increments if all needs > 0.4, resets otherwise.
    """
    all_stable = all(v > 0.4 for v in agent.needs.levels.values())
    if all_stable:
        agent.ticks_survival_stable += 1
    else:
        agent.ticks_survival_stable = 0


# ---------------------------------------------------------------------------
# Drive tracking after actions
# ---------------------------------------------------------------------------

def update_drive_tracking(agent: AgentState, action_type: str) -> None:
    """Update drive-related tracking fields after an action.

    Called after each action execution. Maintains the recent_actions
    list (last 20 actions) for novelty computation.
    """
    agent.recent_actions.append(action_type)
    # Keep only last 20 actions
    if len(agent.recent_actions) > 20:
        agent.recent_actions = agent.recent_actions[-20:]


# ---------------------------------------------------------------------------
# Inner Life prompt generation — the core of the drive system
# ---------------------------------------------------------------------------

def is_agent_in_settlement(agent: AgentState, config: SimulationConfig, world_state: "WorldState | None" = None) -> bool:
    """Check if agent is in a settlement area (enough structures nearby)."""
    if world_state is None:
        return False
    from src.engine.structures import is_in_settlement
    return is_in_settlement(agent.position, world_state.tiles, config)


def format_inner_life(
    agent: AgentState,
    config: SimulationConfig,
    world_state: "WorldState | None" = None,
) -> str:
    """Format the 'Inner Life' section of the agent prompt.

    Returns descriptive felt-state text for all active drives. Higher
    drives only appear when the agent has unlocked that Maslow level.
    The text is evocative, not prescriptive — it describes what the
    agent FEELS, not what it should DO.
    """
    lines: list[str] = []
    level = agent.maslow_level

    # --- Level 2: Safety / Planning ---
    if level >= 2:
        has_reserves = len(agent.inventory) > 0
        has_shelter = False
        if world_state:
            tile = world_state.tiles[agent.position.x][agent.position.y]
            has_shelter = any(
                s.structure_type.value == "shelter" and s.health > 0
                for s in tile.structures
            )

        if not has_reserves and not has_shelter:
            lines.append(
                "You are fed and watered for now. But you have nothing saved — "
                "no reserves in your inventory, no shelter overhead. "
                "If the resources on this tile deplete or your needs spike, you have nothing to fall back on."
            )
        elif not has_shelter:
            lines.append(
                "You have some resources in reserve. But there is no shelter here — "
                "nothing to slow your degradation if times get hard."
            )

    # --- Level 3: Social Belonging ---
    if level >= 3:
        # Settlement awareness
        in_settlement = is_agent_in_settlement(agent, config, world_state)

        # Check for group vs solitude
        nearby_count = len(agent.agents_in_perception)
        if nearby_count == 0:
            lines.append(
                "You are alone. No other entity is within reach. "
                "No one can hear you, help you, or know if you are struggling."
            )
        elif in_settlement:
            lines.append(
                "You are in a settled area — structures cluster around you, "
                "built by the work of many hands. This place has become something more "
                "than raw wilderness. It feels like home."
            )
        elif nearby_count >= 2:
            # Check if they have shared creation
            if agent.structures_built_count == 0:
                familiar_ids = [
                    aid for aid in agent.agents_in_perception
                    if aid in agent.relationships
                    and agent.relationships[aid].interaction_count >= 3
                ]
                if familiar_ids:
                    entities_str = " and ".join(f"Entity {aid}" for aid in familiar_ids[:3])
                    lines.append(
                        f"You have been near {entities_str} for a while now. You talk, you share this space. "
                        f"But you have built nothing together — no shared home, no shared project. "
                        f"Is this a group, or just entities who happen to be nearby?"
                    )

    # --- Level 4: Esteem ---
    if level >= 4:
        if agent.structures_built_count == 0 and not agent.innovations_proposed:
            lines.append(
                "What have you accomplished beyond survival? You have gathered and eaten. "
                "Every entity does this. Nothing distinguishes what you have done from what anyone else has done."
            )
        # Recognition
        # Simple proxy: if agent has specialisations, they have some status
        if not agent.specialisations and agent.structures_built_count == 0:
            lines.append(
                "No other entity has ever referenced anything you have done. "
                "You are known to others only as someone who gathers and eats."
            )

    # --- Level 5: Cognitive ---
    if level >= 5:
        # Exploration coverage
        total_tiles = config.grid_width * config.grid_height
        explored_pct = len(agent.visited_tiles) / total_tiles * 100
        if explored_pct < 30:
            lines.append(
                f"You have explored {explored_pct:.0f}% of the world you could reach. "
                f"There are tiles you have never visited, resources you have never seen."
            )

        # Teaching drive
        if agent.specialisations and agent.activity_counts:
            top_activity = max(agent.activity_counts, key=agent.activity_counts.get)
            count = agent.activity_counts[top_activity]
            if count >= 10:
                lines.append(
                    f"You have done '{top_activity}' {count} times — you understand it better than most. "
                    f"But you have never shared this knowledge with anyone."
                )

    # --- Level 6: Creative ---
    if level >= 6:
        if agent.structures_built_count == 0:
            lines.append(
                "You have seen enough of this world to know it could be shaped. "
                "The raw materials are there. Your hands itch to make something — "
                "something that didn't exist before, something that says you were here. "
                "You have never built anything."
            )
        elif agent.structures_built_count < 3:
            lines.append(
                f"You have built {agent.structures_built_count} structure{'s' if agent.structures_built_count > 1 else ''}. "
                f"The act of creation felt meaningful. There is more you could make."
            )

        # Novelty — action repetition
        if agent.recent_actions:
            unique_recent = set(agent.recent_actions[-10:])
            all_possible = {"gather", "consume", "move", "communicate", "build",
                           "store", "innovate", "compose", "propose_rule", "wait"}
            never_tried = all_possible - set(agent.activity_counts.keys())
            # Only show if they've been repetitive AND there are untried actions
            if len(unique_recent) <= 3 and never_tried:
                recent_str = ", ".join(sorted(unique_recent))
                untried_str = ", ".join(sorted(never_tried - {"wait", "done"}))
                if untried_str:
                    lines.append(
                        f"Your recent actions have been repetitive: {recent_str}. "
                        f"You have never tried: {untried_str}."
                    )

    # --- Level 7: Self-Actualisation ---
    if level >= 7:
        if not agent.innovations_proposed:
            lines.append(
                "You have built with what exists. But you feel a pull toward creating "
                "something truly new — something that has never existed in this world before. "
                "What would you invent if you could invent anything?"
            )
        if not agent.goals:
            lines.append(
                "You have survived, you have built. But to what end? "
                "What is your purpose here? What are you working toward?"
            )

    # --- Level 8: Transcendence ---
    if level >= 8:
        lines.append(
            "You have created, innovated, and been recognised. "
            "But what about the others? What could all of you build together "
            "that none of you could build alone? What would you leave behind "
            "for entities who come after you?"
        )

    if not lines:
        # Survival mode — no higher drives active yet
        return "Your focus is on immediate survival. Higher concerns feel distant."

    return "\n\n".join(lines)
