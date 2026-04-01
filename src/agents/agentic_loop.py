"""Agentic ReAct loop for Agent Civilisation.

Implements a lightweight Reason-Act-Observe loop that gives agents genuine
agency: they can set goals, form plans, execute multi-step turns, and observe
the results of their actions before deciding what to do next.

Each agentic turn runs up to config.max_steps_per_agentic_turn iterations:
  1. REASON: Send state + perception + memory + goals + plan + situation to LLM
  2. ACT: Parse response, execute the action on the world
  3. OBSERVE: Re-perceive the world, update agent state
  4. Repeat or exit (if agent says "done" or step cap reached)
"""

from __future__ import annotations

import logging
import random
import re
from typing import Any

from src.config import SimulationConfig
from src.types import (
    Action,
    ActionType,
    AgentState,
    BusEvent,
    BusEventType,
    Event,
    EventBus,
    MemoryEntry,
    Message,
    Position,
    RelationshipRecord,
    WorldState,
    WELLBEING_MAX,
)
from src.engine.world import World
from src.engine.structures import (
    build_structure,
    can_build,
    describe_structures,
    get_gathering_bonus,
    get_path_cost_multiplier,
    get_storage_contents,
    is_in_settlement,
    count_structures_nearby,
    read_marker,
    repair_structure,
    store_resource,
)
from src.agents.llm import LLMClient
from src.agents.memory import MemoryStore
from src.agents.perception import visible_tiles, visible_resources, visible_agents
from src.agents.specialisation import (
    record_activity,
    get_efficiency_bonus,
    describe_specialisations,
    describe_activity_progress,
    apply_teaching,
)
from src.agents.drives import format_inner_life, update_drive_tracking

logger = logging.getLogger("agent_civilisation.agentic_loop")


# ======================================================================
# Direction parsing map (shared with decision.py conventions)
# ======================================================================

_DIRECTION_MAP: dict[str, tuple[int, int]] = {
    "north": (0, -1),
    "south": (0, 1),
    "east": (1, 0),
    "west": (-1, 0),
    "northeast": (1, -1),
    "northwest": (-1, -1),
    "southeast": (1, 1),
    "southwest": (-1, 1),
    "up": (0, -1),
    "down": (0, 1),
    "right": (1, 0),
    "left": (-1, 0),
}


def _sign(n: int) -> int:
    """Return -1, 0, or 1 depending on sign of n."""
    if n > 0:
        return 1
    elif n < 0:
        return -1
    return 0


# ======================================================================
# AgenticLoop
# ======================================================================

class AgenticLoop:
    """Runs one agentic turn for an agent using a ReAct loop.

    Each turn: up to config.max_steps_per_agentic_turn iterations of:
      1. REASON: Send state + perception + memory + goals + plan to LLM
      2. ACT: Parse response, execute the action on the world
      3. OBSERVE: Re-perceive the world, update agent state
      4. Repeat or exit (if agent says "done" or step cap reached)
    """

    def __init__(
        self,
        config: SimulationConfig,
        llm_client: LLMClient,
        event_bus: EventBus,
    ) -> None:
        self.config = config
        self.llm_client = llm_client
        self.bus = event_bus
        self._rng = random.Random()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def run_turn(
        self,
        agent: AgentState,
        triggering_events: list[Event],
        world: World,
        world_state: WorldState,
    ) -> list[Action]:
        """Run a full agentic turn for *agent*. Returns all actions taken."""
        self.world_state = world_state  # available for prompt construction
        actions_taken: list[Action] = []
        tick = world_state.tick

        # Emit AGENTIC_TURN_START
        await self.bus.emit(BusEvent(
            type=BusEventType.AGENTIC_TURN_START,
            tick=tick,
            agent_id=agent.id,
            data={"triggers": [e.type.value for e in triggering_events]},
        ))

        # Build initial context from the agent's perception
        context = self._build_context(agent, triggering_events, world, world_state)

        # Record detected events as memories
        memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
        for ev in triggering_events:
            memory_store.record_event(ev)

        for step in range(self.config.max_steps_per_agentic_turn):
            # 1. REASON: call LLM
            prompt = self._build_agentic_prompt(agent, context, step)
            response = await self.llm_client.call_llm(prompt)

            # If the LLM is unreachable (fallback response), don't burn more steps
            if response == "I will wait and observe." and step > 0:
                break

            # Emit REASONING_STEP
            await self.bus.emit(BusEvent(
                type=BusEventType.REASONING_STEP,
                tick=tick,
                agent_id=agent.id,
                data={"step": step, "response": response[:500]},
            ))

            # 2. ACT: parse response into actions
            # The LLM may set a goal AND take a physical action in one response.
            parsed = self._parse_agentic_response(response, agent, world_state)

            # Handle meta-actions inline (goal, plan) — these don't consume a step
            physical_action: Action | None = None

            for action in parsed:
                if action.type == ActionType.SET_GOAL:
                    self._apply_goal(agent, action)
                    await self.bus.emit(BusEvent(
                        type=BusEventType.GOAL_SET,
                        tick=tick,
                        agent_id=agent.id,
                        data={"goal": action.goal or ""},
                    ))
                    # Record goal change as memory
                    goal_ms = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
                    goal_ms.record_goal_change(action.goal or "", tick, is_new=True)

                elif action.type == ActionType.UPDATE_PLAN:
                    self._apply_plan(agent, action)
                    await self.bus.emit(BusEvent(
                        type=BusEventType.PLAN_UPDATED,
                        tick=tick,
                        agent_id=agent.id,
                        data={"plan": agent.plan},
                    ))
                    # Record plan change as memory
                    plan_ms = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
                    plan_ms.record_plan_change(agent.plan, tick)

                elif action.type == ActionType.DONE:
                    # Agent explicitly ends its turn
                    await self.bus.emit(BusEvent(
                        type=BusEventType.AGENTIC_TURN_END,
                        tick=tick,
                        agent_id=agent.id,
                        data={
                            "reason": "agent_done",
                            "steps": step + 1,
                            "actions_count": len(actions_taken),
                        },
                    ))
                    return actions_taken

                else:
                    # Physical action (MOVE, GATHER, COMMUNICATE, BUILD, CONSUME, STORE, GIVE, READ_MARKER, WAIT)
                    physical_action = action

            # If no physical action was parsed but goal/plan were set,
            # continue to next step to get a physical action
            if physical_action is None:
                continue

            # Execute the physical action on the world
            action_feedback, build_succeeded = await self._execute_action(agent, physical_action, world, world_state)
            actions_taken.append(physical_action)

            # Track activity for specialisation and drives
            update_drive_tracking(agent, physical_action.type.value)
            new_spec = record_activity(agent, physical_action.type.value, self.config)
            if new_spec:
                await self.bus.emit(BusEvent(
                    type=BusEventType.SPECIALISATION_GAINED,
                    tick=tick,
                    agent_id=agent.id,
                    data={
                        "activity": new_spec,
                        "count": agent.activity_counts.get(new_spec, 0),
                    },
                ))

            # Emit ACTION_TAKEN
            await self.bus.emit(BusEvent(
                type=BusEventType.ACTION_TAKEN,
                tick=tick,
                agent_id=agent.id,
                data={
                    "action": physical_action.type.value,
                    "reasoning": physical_action.reasoning,
                },
            ))

            # Emit specific structure bus events
            if physical_action.type == ActionType.BUILD and build_succeeded:
                await self.bus.emit(BusEvent(
                    type=BusEventType.STRUCTURE_BUILT,
                    tick=tick,
                    agent_id=agent.id,
                    data={
                        "structure_type": physical_action.structure_type or "unknown",
                        "position": {"x": agent.position.x, "y": agent.position.y},
                    },
                ))
            elif physical_action.type == ActionType.CONSUME:
                await self.bus.emit(BusEvent(
                    type=BusEventType.RESOURCE_CONSUMED,
                    tick=tick,
                    agent_id=agent.id,
                    data={"resource_type": physical_action.resource_type or "unknown"},
                ))
            elif physical_action.type == ActionType.STORE:
                await self.bus.emit(BusEvent(
                    type=BusEventType.RESOURCE_STORED,
                    tick=tick,
                    agent_id=agent.id,
                    data={
                        "resource_type": physical_action.resource_type or "unknown",
                        "position": {"x": agent.position.x, "y": agent.position.y},
                    },
                ))
            elif physical_action.type == ActionType.READ_MARKER:
                await self.bus.emit(BusEvent(
                    type=BusEventType.MARKER_READ,
                    tick=tick,
                    agent_id=agent.id,
                    data={"position": {"x": agent.position.x, "y": agent.position.y}},
                ))
            elif physical_action.type == ActionType.GIVE and not action_feedback:
                await self.bus.emit(BusEvent(
                    type=BusEventType.RESOURCE_GIVEN,
                    tick=tick,
                    agent_id=agent.id,
                    data={
                        "resource_type": physical_action.resource_type or "unknown",
                        "target_agent_id": physical_action.target_agent_id,
                    },
                ))

            # Bus events for compose/innovation/rules are emitted inside
            # their execute methods since they need outcome data (success/fail).

            # 3. OBSERVE: re-perceive the world
            observation = self._observe(agent, physical_action, world, world_state, action_feedback)
            context["observations"].append(observation)

            # Emit OBSERVATION
            await self.bus.emit(BusEvent(
                type=BusEventType.OBSERVATION,
                tick=tick,
                agent_id=agent.id,
                data={"observation": observation[:300]},
            ))

            # Record a memory of this step
            memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
            memory_store.add(MemoryEntry(
                tick=tick,
                summary=f"Step {step}: {physical_action.reasoning[:100]}",
                importance=0.6,
            ))

        # Step cap reached — emit turn end
        await self.bus.emit(BusEvent(
            type=BusEventType.AGENTIC_TURN_END,
            tick=tick,
            agent_id=agent.id,
            data={
                "reason": "step_cap",
                "steps": self.config.max_steps_per_agentic_turn,
                "actions_count": len(actions_taken),
            },
        ))

        return actions_taken

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    def _build_context(
        self,
        agent: AgentState,
        triggering_events: list[Event],
        world: World,
        world_state: WorldState,
    ) -> dict[str, Any]:
        """Build the initial context dict that accumulates observations."""
        # Perception
        vis_tiles = visible_tiles(
            agent.position,
            agent.capabilities.perception_range,
            world.tiles,
        )
        vis_resources = visible_resources(
            agent.position,
            agent.capabilities.perception_range,
            world.tiles,
        )
        vis_agents_list = visible_agents(agent, world_state.agents)

        # Format resources — separate "on your tile" from "nearby" so agents know what's gatherable
        resources_here: list[str] = []
        resources_nearby: list[str] = []
        for pos, res in vis_resources:
            label = f"{res.resource_type} ({res.amount:.2f}) at [{pos.x}, {pos.y}]"
            if pos.x == agent.position.x and pos.y == agent.position.y:
                resources_here.append(label)
            else:
                resources_nearby.append(label)
        resources_desc: list[str] = []
        if resources_here:
            resources_desc.append("ON YOUR TILE (gatherable): " + ", ".join(resources_here))
        if resources_nearby:
            resources_desc.append("NEARBY (move there first): " + ", ".join(resources_nearby))
        if not resources_desc:
            resources_desc.append("none visible")

        # Format nearby agents (include specialisations and state so agents can reason about cooperation)
        agents_desc: list[str] = []
        for other in vis_agents_list:
            dist = agent.position.distance_to(other.position)
            desc = f"Entity {other.id} at [{other.position.x}, {other.position.y}] (distance {dist:.0f})"
            if other.specialisations:
                desc += f" [skills: {', '.join(other.specialisations)}]"
            if other.wellbeing > 0.7:
                desc += " (socially fulfilled)"
            elif other.needs.any_critical():
                desc += " (struggling)"
            agents_desc.append(desc)

        # Format structures on visible tiles
        structures_desc: list[str] = []
        for tile in vis_tiles:
            tile_structs = describe_structures(tile)
            for desc in tile_structs:
                structures_desc.append(f"[{tile.position.x}, {tile.position.y}]: {desc}")

        # Format events
        event_summaries = [e.summary() for e in triggering_events] if triggering_events else ["Routine moment."]

        # Memory summary — with context hints for relevance
        context_hints: list[str] = []
        # Add nearby agent IDs as hints so agent recalls past interactions
        for other in vis_agents_list:
            context_hints.append(f"Agent {other.id}")
            context_hints.append(f"Entity {other.id}")
        # Add current position as hint
        context_hints.append(f"({agent.position.x}, {agent.position.y})")
        context_hints.append(f"[{agent.position.x}, {agent.position.y}]")
        # Add visible resource types
        for _, res in vis_resources:
            context_hints.append(res.resource_type)

        memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
        memory_summary = memory_store.get_summary(max_entries=15, context_hints=context_hints)

        # Collective rules (established norms visible to all agents)
        rules_desc: list[str] = []
        for rule in world_state.collective_rules:
            if rule.established:
                rules_desc.append(f"Rule #{rule.rule_id}: \"{rule.text}\" (established, {rule.adoption_rate:.0%} adoption)")
            else:
                # Show unestablished rules the agent hasn't voted on yet — with incentive
                accepted_count = len(rule.accepted_by)
                total_agents = len(world_state.agents)
                needed = max(0, int(total_agents * self.config.rule_establishment_threshold) - accepted_count + 1)
                if agent.id not in rule.accepted_by and agent.id not in rule.ignored_by:
                    rules_desc.append(
                        f"Rule #{rule.rule_id}: \"{rule.text}\" "
                        f"(proposed by Entity {rule.proposed_by}, {rule.adoption_rate:.0%} adoption, "
                        f"needs {needed} more to establish. "
                        f"BENEFIT IF ESTABLISHED: {self.config.rule_need_depletion_reduction:.0%} slower need depletion for ALL entities. "
                        f"Use ACCEPT_RULE #{rule.rule_id} to vote yes)"
                    )
                elif agent.id in rule.accepted_by:
                    rules_desc.append(
                        f"Rule #{rule.rule_id}: \"{rule.text}\" "
                        f"(you accepted this, {rule.adoption_rate:.0%} adoption, needs {needed} more)"
                    )

        # Discovered recipes (composition knowledge)
        recipes_desc: list[str] = []
        for recipe in world_state.discovered_recipes:
            if recipe.output_name in agent.known_recipes:
                recipes_desc.append(f"{' + '.join(recipe.inputs)} -> {recipe.output_name}: {recipe.output_description}")

        # Settlement detection
        in_settlement = is_in_settlement(agent.position, world_state.tiles, self.config)
        nearby_structure_count = count_structures_nearby(
            agent.position,
            self.config.settlement_range,
            world_state.tiles,
            self.config.grid_width,
            self.config.grid_height,
        )

        return {
            "resources": resources_desc,
            "agents": agents_desc,
            "structures": structures_desc,
            "events": event_summaries,
            "memory_summary": memory_summary,
            "rules": rules_desc,
            "recipes": recipes_desc,
            "in_settlement": in_settlement,
            "nearby_structure_count": nearby_structure_count,
            "observations": [],  # accumulates during the turn
        }

    # ------------------------------------------------------------------
    # Prompt builder
    # ------------------------------------------------------------------

    def _build_agentic_prompt(
        self,
        agent: AgentState,
        context: dict[str, Any],
        step: int,
    ) -> str:
        """Build the LLM prompt for a single reasoning step.

        CRITICAL: No human behavioral instructions. No names, no personalities,
        no social norms. Just state, perception, memory, and available actions.
        """
        needs_str = ", ".join(
            f"{k}: {v:.2f}" for k, v in agent.needs.levels.items()
        )
        caps = agent.capabilities

        resources_str = ", ".join(context["resources"]) if context["resources"] else "none visible"
        agents_str = ", ".join(context["agents"]) if context["agents"] else "none visible"
        structures_str = ", ".join(context["structures"]) if context["structures"] else "none visible"
        rules_str = "\n  ".join(context.get("rules", [])) if context.get("rules") else "none"
        recipes_str = ", ".join(context.get("recipes", [])) if context.get("recipes") else "none known"

        # Build relationship context for nearby agents
        rel_parts: list[str] = []
        for other_id in agent.agents_in_perception:
            if other_id in agent.relationships:
                rel = agent.relationships[other_id]
                quality = "positive" if rel.positive_count > rel.negative_count else "neutral" if rel.negative_count == 0 else "strained"
                bond_label = ", bonded" if rel.is_bonded else ""
                rel_parts.append(
                    f"Entity {other_id}: {rel.interaction_count} past interactions ({quality}{bond_label}), last met tick {rel.last_interaction_tick}"
                )
            elif other_id in agent.met_agents:
                rel_parts.append(f"Entity {other_id}: briefly encountered before, no deep interaction")
        for other_id in agent.agents_in_perception:
            if other_id not in agent.relationships and other_id not in agent.met_agents:
                rel_parts.append(f"Entity {other_id}: stranger (never met)")
        relationships_str = "\n".join(rel_parts) if rel_parts else "No nearby entities with known history."

        # Inventory
        if agent.inventory:
            inventory_str = ", ".join(agent.inventory) + f" ({len(agent.inventory)}/{self.config.agent_carry_capacity})"
        else:
            inventory_str = f"empty (0/{self.config.agent_carry_capacity})"

        # Goals and plan
        goals_str = "; ".join(agent.goals) if agent.goals else "none"
        plan_str = " -> ".join(agent.plan) if agent.plan else "none"

        # Specialisations
        spec_str = describe_specialisations(agent, self.config)
        activity_str = describe_activity_progress(agent, self.config)

        # Settlement status
        settlement_str = ""
        if context.get("in_settlement"):
            nearby_count = context.get("nearby_structure_count", 0)
            settlement_str = f"\nSETTLEMENT: You are in a settled area ({nearby_count} structures nearby). Benefits: slower need drain, wellbeing bonus. More structures = stronger settlement."
        elif context.get("nearby_structure_count", 0) >= 2:
            nearby_count = context["nearby_structure_count"]
            needed = self.config.settlement_structure_threshold
            settlement_str = f"\nNEARBY STRUCTURES: {nearby_count} structures within range ({needed} needed for settlement bonuses). Building more here would create a settlement."

        # Situation: initial events on step 0, then observations
        if step == 0:
            situation_str = "\n".join(context["events"])
        else:
            # For subsequent steps, show the most recent observation
            if context["observations"]:
                situation_str = context["observations"][-1]
            else:
                situation_str = "Continuing your turn."

        # Previous observations (for multi-step context)
        prev_observations = ""
        if step > 0 and context["observations"]:
            obs_lines = [f"  Step {i}: {obs}" for i, obs in enumerate(context["observations"])]
            prev_observations = f"\nPrevious observations this turn:\n" + "\n".join(obs_lines)

        # Inner life — Maslow drives as felt states
        inner_life_str = format_inner_life(agent, self.config, self.world_state)

        # Build dynamic innovation recipe lines for the BUILD section
        innovation_build_lines = ""
        if self.world_state and self.world_state.discovered_recipes:
            for recipe in self.world_state.discovered_recipes:
                if recipe.output_name in agent.known_recipes:
                    build_name = recipe.output_name.lower().replace(" ", "_")
                    reqs = " + ".join(recipe.inputs)
                    innovation_build_lines += f"\n  * {recipe.output_name} ({reqs}) — {recipe.output_description} [command: BUILD {build_name}]"

        prompt = f"""You exist in a world alongside other entities like you. You were not given a name, a role, or instructions on how to behave. What you do is up to you.

Think out loud — express your inner thoughts naturally, as if talking to yourself. What do you notice? What do you want? What worries you? What interests you? Be specific and personal.

YOUR STATE:
- Position: [{agent.position.x}, {agent.position.y}]
- Needs: [{needs_str}] (these are your survival resources — when they drop low, your capabilities degrade. Gather resources from nearby tiles, then consume them from your inventory to restore needs.)
- Capabilities: perception range {caps.perception_range:.1f}, movement speed {caps.movement_speed:.1f}
- Carrying: {inventory_str}

YOUR INNER LIFE:
{inner_life_str}

WHAT YOU CAN PERCEIVE:
- Nearby resources: {resources_str}
- Nearby entities: {agents_str}
- Structures: {structures_str}
- Collective rules/norms: {rules_str}
- Known recipes: {recipes_str}

YOUR RELATIONSHIPS WITH NEARBY ENTITIES:
{relationships_str}

YOUR MEMORY:
{context["memory_summary"]}

YOUR SPECIALISATIONS: {spec_str}
YOUR EXPERIENCE: {activity_str}
YOUR GOALS: {goals_str}
YOUR PLAN: {plan_str}{settlement_str}

CURRENT SITUATION: {situation_str}{prev_observations}

HOW THE WORLD WORKS:
- GATHER resources from the tile you're standing on (e.g. "gather water"). You can ONLY gather from your current tile — if the resource is nearby, MOVE there first. Adds to your inventory.
- CONSUME resources from inventory to restore needs (e.g. "consume food").
- BUILD structures if you have the required resources in your inventory:
  * Shelter (water + material) — reduces how fast your capabilities degrade when needs are low.
  * Storage (food + material) — stores resources on this tile for anyone to access later.
  * Marker (material) — leaves a persistent message that others can read.
  * Path (material + material) — makes this tile easier and faster to cross.{innovation_build_lines}
- REPAIR — spend 1 material from your inventory to repair the most damaged structure on your tile. Keeps infrastructure alive.
- GIVE resource to Entity N — transfer a resource from your inventory to a nearby entity (e.g. "give water to Entity 5"). You must be within communication range.
- COMMUNICATE "message" or COMMUNICATE "message" to Entity N — talk to nearby entities. Entities you interact with often develop stronger bonds, which provide greater social wellbeing.
- MOVE north/south/east/west (or diagonals), or MOVE toward Entity N, or MOVE to [x, y].
- SET_GOAL and UPDATE_PLAN to organise your thinking.
- COMPOSE structure1 + structure2: Combine two structures on your tile — the combination creates something new with unique properties.
- PROPOSE_INNOVATION "description": Describe a new type of structure you want to invent. If feasible, it becomes a recipe everyone can learn.
- PROPOSE_RULE "text": Propose a collective agreement for all entities. Others can ACCEPT_RULE #id or IGNORE_RULE #id. When enough entities accept, the rule becomes an established norm.
- STORE resources in a storage structure, READ_MARKER to read messages left by others.
- WAIT if you want to stay put, DONE to end your turn.

THINGS YOU'VE NOTICED ABOUT THIS WORLD:
- Building structures in the same area creates compounding benefits — the land becomes more productive. Resources regenerate faster near structures.
- Multiple shelters on a tile compound their protective effect. Multiple paths compound their speed.
- Areas dense with structures feel different — needs deplete slower, wellbeing rises. This is what a settlement feels like.
- When collective rules become established (enough entities accept them), everyone benefits — needs deplete slower across the whole world. Governance has tangible survival value.
- Entities who have done something many times become masters at it. When a master communicates with others, some of that expertise transfers.
- Structures decay over time. Without repair, everything returns to nothing. Maintaining what exists is as important as building new things.

IMPORTANT: You learn by DOING, not just thinking. Take a physical action every step — gather, move, build, communicate, explore. If unsure, gather resources or move toward another entity. Reflection is valuable, but act on your reflections.

What are you thinking? What do you do next?"""

        return prompt

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_agentic_response(
        self,
        response: str,
        agent: AgentState,
        world_state: WorldState,
    ) -> list[Action]:
        """Parse the LLM's free-text response into one or more Actions.

        May return multiple actions (e.g. set_goal + move). Meta-actions
        (SET_GOAL, UPDATE_PLAN) come first, followed by at most one
        physical action.
        """
        text = response.strip()
        text_lower = text.lower()
        actions: list[Action] = []

        # --- set_goal ---
        goal_match = re.search(
            r'set_goal\s+["\'\[]?(.+?)["\'\]]?\s*(?:\n|$|\.)',
            text,
            re.IGNORECASE,
        )
        if not goal_match:
            goal_match = re.search(
                r'goal:\s*["\'\[]?(.+?)["\'\]]?\s*(?:\n|$)',
                text,
                re.IGNORECASE,
            )
        if goal_match:
            goal_text = goal_match.group(1).strip().rstrip(".")
            if goal_text:
                actions.append(Action(
                    type=ActionType.SET_GOAL,
                    goal=goal_text,
                    reasoning=text[:200],
                ))

        # --- update_plan ---
        plan_match = re.search(
            r'update_plan\s+["\'\[]?(.+?)["\'\]]?\s*(?:\n|$)',
            text,
            re.IGNORECASE,
        )
        if not plan_match:
            plan_match = re.search(
                r'plan:\s*["\'\[]?(.+?)["\'\]]?\s*(?:\n|$)',
                text,
                re.IGNORECASE,
            )
        if plan_match:
            plan_text = plan_match.group(1).strip()
            # Split on pipe delimiter
            steps = [s.strip() for s in plan_text.split("|") if s.strip()]
            if steps:
                actions.append(Action(
                    type=ActionType.UPDATE_PLAN,
                    plan_steps=steps,
                    reasoning=text[:200],
                ))

        # --- done / end turn ---
        if re.search(r'(?:^|\.\s+)(?:done|end\s+turn)\s*[.!]?\s*$', text_lower, re.MULTILINE):
            actions.append(Action(
                type=ActionType.DONE,
                reasoning=text[:200],
            ))
            return actions  # done overrides any physical action

        # --- propose_rule ---
        rule_match = re.search(
            r'propose_rule\s+["\'\[]?(.+?)["\'\]]?\s*(?:\n|$)',
            text,
            re.IGNORECASE,
        )
        if rule_match:
            rule_text = rule_match.group(1).strip().rstrip(".")
            if rule_text:
                actions.append(Action(
                    type=ActionType.PROPOSE_RULE,
                    rule_text=rule_text,
                    reasoning=text[:200],
                ))
                return actions

        # --- accept_rule ---
        accept_match = re.search(r'accept_rule\s+#?(\d+)', text_lower)
        if accept_match:
            actions.append(Action(
                type=ActionType.ACCEPT_RULE,
                rule_id=int(accept_match.group(1)),
                reasoning=text[:200],
            ))
            return actions

        # --- ignore_rule ---
        ignore_match = re.search(r'ignore_rule\s+#?(\d+)', text_lower)
        if ignore_match:
            actions.append(Action(
                type=ActionType.IGNORE_RULE,
                rule_id=int(ignore_match.group(1)),
                reasoning=text[:200],
            ))
            return actions

        # --- compose ---
        compose_match = re.search(
            r'compose\s+(\w+)\s*\+\s*(\w+)',
            text,
            re.IGNORECASE,
        )
        if compose_match:
            targets = [compose_match.group(1).lower(), compose_match.group(2).lower()]
            actions.append(Action(
                type=ActionType.COMPOSE,
                compose_targets=sorted(targets),
                reasoning=text[:200],
            ))
            return actions

        # --- propose_innovation ---
        innovation_match = re.search(
            r'propose_innovation\s+["\'\[]?(.+?)["\'\]]?\s*(?:\n|$)',
            text,
            re.IGNORECASE,
        )
        if innovation_match:
            desc = innovation_match.group(1).strip().rstrip(".")
            if desc:
                actions.append(Action(
                    type=ActionType.PROPOSE_INNOVATION,
                    innovation_description=desc,
                    reasoning=text[:200],
                ))
                return actions

        # --- build ---
        # Match base types + any discovered recipe names (innovations/compositions)
        valid_build_types = ["shelter", "storage", "marker", "path"]
        for recipe in world_state.discovered_recipes:
            # Add both underscore and space forms: "communication_beacon" + "communication beacon"
            normalized = recipe.output_name.lower().replace(" ", "_")
            if normalized not in valid_build_types:
                valid_build_types.append(normalized)
            spaced = recipe.output_name.lower()
            if spaced != normalized and spaced not in valid_build_types:
                valid_build_types.append(spaced)
        build_types_pattern = "|".join(re.escape(t) for t in valid_build_types)
        build_match = re.search(
            rf'build\s+(?:a\s+|the\s+)?({build_types_pattern})(?:\s+["\'](.+?)["\'])?',
            text,
            re.IGNORECASE,
        )
        if build_match:
            # Normalize to underscore form for lookup
            structure_type = build_match.group(1).lower().replace(" ", "_")
            marker_msg = build_match.group(2) if build_match.lastindex and build_match.lastindex >= 2 else None
            actions.append(Action(
                type=ActionType.BUILD,
                structure_type=structure_type,
                marker_message=marker_msg,
                reasoning=text[:200],
            ))
            return actions

        # --- consume ---
        # Only match valid resource types — prevents "consume this" / "consume something" garbage
        consume_match = re.search(r'consume\s+(?:some\s+|the\s+|my\s+)?(water|food|material)', text_lower)
        if consume_match:
            resource = consume_match.group(1)
            actions.append(Action(
                type=ActionType.CONSUME,
                resource_type=resource,
                reasoning=text[:200],
            ))
            return actions

        # --- store ---
        # Only match valid resource types
        store_match = re.search(r'store\s+(?:some\s+|the\s+|my\s+)?(water|food|material)', text_lower)
        if store_match:
            resource = store_match.group(1)
            actions.append(Action(
                type=ActionType.STORE,
                resource_type=resource,
                reasoning=text[:200],
            ))
            return actions

        # --- repair ---
        if re.search(r'\brepair\b', text_lower):
            actions.append(Action(
                type=ActionType.REPAIR,
                reasoning=text[:200],
            ))
            return actions

        # --- give ---
        give_match = re.search(
            r'give\s+(?:some\s+|a\s+|my\s+)?(water|food|material)\s+to\s+(?:entity|agent)\s*(\d+)',
            text_lower,
        )
        if give_match:
            resource = give_match.group(1)
            target_id = int(give_match.group(2))
            actions.append(Action(
                type=ActionType.GIVE,
                resource_type=resource,
                target_agent_id=target_id,
                reasoning=text[:200],
            ))
            return actions

        # --- read_marker ---
        if re.search(r'\bread_marker\b', text_lower) or re.search(r'\bread\s+marker\b', text_lower):
            actions.append(Action(
                type=ActionType.READ_MARKER,
                reasoning=text[:200],
            ))
            return actions

        # --- communicate ---
        comm_message: str | None = None
        comm_target_id: int = -1

        # Priority 1: Quoted message to specific entity
        # "Entity 8: 'Hey there!'" or "communicate 'hello' to entity 7"
        quoted_target = re.search(
            r'(?:communicate|say|tell|send\s+message)\s+["\'](.+?)["\']\s+to\s+(?:entity|agent)\s*(\d+)',
            text, re.IGNORECASE,
        )
        if not quoted_target:
            quoted_target = re.search(
                r'(?:communicate|say|tell|send\s+message)\s+to\s+(?:entity|agent)\s*(\d+)\s*[:]\s*["\'](.+?)["\']',
                text, re.IGNORECASE,
            )
            if quoted_target:
                # Swap groups — target is group 1, message is group 2 in this pattern
                comm_target_id = int(quoted_target.group(1))
                comm_message = quoted_target.group(2).strip()
                quoted_target = True  # signal we found it

        if quoted_target and comm_message is None:
            comm_message = quoted_target.group(1).strip()
            comm_target_id = int(quoted_target.group(2))

        # Priority 2: Quoted message (no target)
        if comm_message is None:
            quoted_broad = re.search(
                r'(?:communicate|say|tell)\s+["\'](.+?)["\']',
                text, re.IGNORECASE,
            )
            if quoted_broad:
                comm_message = quoted_broad.group(1).strip()

        # Priority 3: "Entity N: message" pattern (agents naturally format this way)
        if comm_message is None:
            entity_msg = re.search(
                r'(?:entity|agent)\s*(\d+)\s*[:]\s*["\'](.+?)["\']',
                text, re.IGNORECASE,
            )
            if entity_msg:
                comm_target_id = int(entity_msg.group(1))
                comm_message = entity_msg.group(2).strip()

        # Priority 4: Unquoted "communicate X to entity N"
        if comm_message is None:
            unquoted_target = re.search(
                r'(?:communicate|say|tell|send\s+message)\s+(.+?)\s+to\s+(?:entity|agent)\s*(\d+)',
                text, re.IGNORECASE,
            )
            if unquoted_target:
                msg = unquoted_target.group(1).strip().rstrip(".")
                # Filter out reasoning fragments
                if not re.match(r'^(with|about|before|after|but|more|that|this|it)\b', msg.lower()):
                    comm_message = msg
                    comm_target_id = int(unquoted_target.group(2))

        # Priority 5: Unquoted "communicate X" broadcast (most permissive)
        if comm_message is None:
            unquoted_broad = re.search(
                r'(?:communicate|say|tell)\s+(.+?)\s*$',
                text, re.IGNORECASE | re.MULTILINE,
            )
            if unquoted_broad:
                msg = unquoted_broad.group(1).strip().rstrip(".")
                # Filter out reasoning fragments that start with prepositions/pronouns
                if not re.match(r'^(with|about|before|after|but|more|that|this|it|them|something)\b', msg.lower()):
                    comm_message = msg

        if comm_message:
            actions.append(Action(
                type=ActionType.COMMUNICATE,
                message=comm_message,
                target_agent_id=comm_target_id,
                reasoning=text[:200],
            ))
            return actions

        # --- gather ---
        # Only match valid resource types — prevents "gather some" / "gather everything" garbage
        gather_match = re.search(r'gather\s+(?:some\s+|the\s+)?(water|food|material)', text_lower)
        if gather_match:
            resource = gather_match.group(1)
            actions.append(Action(
                type=ActionType.GATHER,
                resource_type=resource,
                reasoning=text[:200],
            ))
            return actions

        # --- move ---
        # Move toward coordinates: "move to [14, 2]" or "move toward 14,2"
        move_to_match = re.search(
            r'move\s+(?:to|toward|towards)\s+\[?(\d+)[,\s]+(\d+)\]?',
            text_lower,
        )
        if move_to_match:
            target_x = int(move_to_match.group(1))
            target_y = int(move_to_match.group(2))
            dx = _sign(target_x - agent.position.x)
            dy = _sign(target_y - agent.position.y)
            if dx != 0 or dy != 0:
                actions.append(Action(
                    type=ActionType.MOVE,
                    direction=(dx, dy),
                    reasoning=text[:200],
                ))
                return actions

        # Move toward entity: "move toward Entity 7" or "move to agent 3"
        move_entity_match = re.search(
            r'move\s+(?:to|toward|towards)\s+(?:entity|agent)\s*(\d+)',
            text_lower,
        )
        if move_entity_match:
            target_id = int(move_entity_match.group(1))
            if target_id in world_state.agents:
                other = world_state.agents[target_id]
                dx = _sign(other.position.x - agent.position.x)
                dy = _sign(other.position.y - agent.position.y)
                if dx != 0 or dy != 0:
                    actions.append(Action(
                        type=ActionType.MOVE,
                        direction=(dx, dy),
                        reasoning=text[:200],
                    ))
                    return actions

        # Cardinal direction: "move north", "move southeast"
        move_match = re.search(
            r'move\s+(north(?:east|west)?|south(?:east|west)?|east|west|up|down|left|right)',
            text_lower,
        )
        if move_match:
            direction_name = move_match.group(1)
            direction = _DIRECTION_MAP.get(direction_name, (0, 0))
            actions.append(Action(
                type=ActionType.MOVE,
                direction=direction,
                reasoning=text[:200],
            ))
            return actions

        # --- wait ---
        if re.search(r'\b(?:wait|observe|stay)\b', text_lower):
            actions.append(Action(
                type=ActionType.WAIT,
                reasoning=text[:200],
            ))
            return actions

        # --- Fallback: wait ---
        if not actions:
            actions.append(Action(
                type=ActionType.WAIT,
                reasoning=text[:200],
            ))

        return actions

    # ------------------------------------------------------------------
    # Action execution (mid-turn, on the live world)
    # ------------------------------------------------------------------

    async def _execute_action(
        self,
        agent: AgentState,
        action: Action,
        world: World,
        world_state: WorldState,
    ) -> tuple[str, bool]:
        """Execute a physical action on the world.

        This happens MID-TURN so the agent can observe the result and
        decide what to do next.

        Returns (action_feedback, build_succeeded) so results are per-call
        rather than stored on the shared instance.
        """
        tick = world_state.tick
        ms = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
        feedback = ""
        build_succeeded = False

        if action.type == ActionType.MOVE:
            pos_before = (agent.position.x, agent.position.y)
            self._execute_move(agent, action, world)
            if (agent.position.x, agent.position.y) == pos_before:
                dir_name = _direction_name(action.direction) if action.direction else "that direction"
                feedback = f"You tried to move {dir_name} but couldn't — the terrain is impassable or you've reached the world boundary."

        elif action.type == ActionType.GATHER:
            inv_before = len(agent.inventory)
            tile = world.get_tile(agent.position.x, agent.position.y)
            gather_bonus = get_gathering_bonus(tile) if tile else 1.0
            self._execute_gather(agent, action, world)
            if len(agent.inventory) > inv_before:
                bonus_note = f" (gathering boosted by {gather_bonus:.0%} from nearby innovation)" if gather_bonus > 1.01 else ""
                ms.add(MemoryEntry(tick=tick, summary=f"Gathered {action.resource_type} at ({agent.position.x}, {agent.position.y}){bonus_note}", importance=0.4))
                if gather_bonus > 1.01:
                    feedback = f"You gathered {action.resource_type}. The nearby innovation structure boosted your yield by {gather_bonus - 1.0:.0%}!"
            elif len(agent.inventory) >= self.config.agent_carry_capacity:
                feedback = f"You tried to gather {action.resource_type} but your inventory is full ({len(agent.inventory)}/{self.config.agent_carry_capacity}). Consume or store resources first."
            else:
                feedback = f"You tried to gather {action.resource_type} but there is none available on this tile. Try moving to a different location."

        elif action.type == ActionType.COMMUNICATE:
            self._execute_communicate(agent, action, world_state)
            # Memory recording is handled inside _deliver_message

        elif action.type == ActionType.BUILD:
            build_succeeded = self._execute_build(agent, action, world, world_state)
            if not build_succeeded:
                stype = action.structure_type or "structure"
                inv_str = ", ".join(agent.inventory) if agent.inventory else "empty"
                # Show what resources are actually needed so agents stop guessing
                recipe_hint = ""
                from src.engine.structures import get_recipe
                base_recipe = get_recipe(stype, self.config)
                if base_recipe:
                    recipe_hint = f" Required: {' + '.join(base_recipe)}."
                else:
                    for r in world_state.discovered_recipes:
                        if r.output_name.lower().replace(" ", "_") == stype.lower().replace(" ", "_"):
                            recipe_hint = f" Required: {' + '.join(r.inputs)}."
                            break
                feedback = f"You tried to build a {stype} but don't have the required resources.{recipe_hint} Your inventory: {inv_str}."

        elif action.type == ActionType.CONSUME:
            consumed = self._execute_consume(agent, action)
            if not consumed:
                rtype = action.resource_type or "unknown"
                inv_str = ", ".join(agent.inventory) if agent.inventory else "empty"
                feedback = f"You tried to consume {rtype} but don't have any in your inventory. Your inventory: {inv_str}."

        elif action.type == ActionType.STORE:
            self._execute_store(agent, action, world)

        elif action.type == ActionType.READ_MARKER:
            self._execute_read_marker(agent, action, world, world_state)

        elif action.type == ActionType.COMPOSE:
            await self._execute_compose(agent, action, world, world_state)
            # Memory recording is handled inside _execute_compose

        elif action.type == ActionType.PROPOSE_INNOVATION:
            await self._execute_propose_innovation(agent, action, world, world_state)
            # Memory recording is handled inside _execute_propose_innovation

        elif action.type == ActionType.PROPOSE_RULE:
            await self._execute_propose_rule(agent, action, world_state)
            if action.rule_text:
                ms.add(MemoryEntry(tick=tick, summary=f"Proposed collective rule: {action.rule_text[:80]}", importance=0.7))

        elif action.type == ActionType.ACCEPT_RULE:
            await self._execute_accept_rule(agent, action, world_state)

        elif action.type == ActionType.IGNORE_RULE:
            await self._execute_ignore_rule(agent, action, world_state)

        elif action.type == ActionType.GIVE:
            give_feedback = self._execute_give(agent, action, world_state)
            if give_feedback:
                feedback = give_feedback
            else:
                rtype = action.resource_type or "resource"
                target = action.target_agent_id
                ms.add(MemoryEntry(tick=tick, summary=f"Gave {rtype} to Entity {target}", importance=0.7))

        elif action.type == ActionType.REPAIR:
            tile = world.get_tile(agent.position.x, agent.position.y)
            if tile is None:
                feedback = "No tile to repair structures on."
            elif "material" not in agent.inventory:
                inv_str = ", ".join(agent.inventory) if agent.inventory else "empty"
                feedback = f"You need material in your inventory to repair. Your inventory: {inv_str}."
            else:
                repaired = repair_structure(agent, tile, self.config)
                if repaired:
                    name = repaired.custom_name or repaired.structure_type.value
                    ms.add(MemoryEntry(tick=tick, summary=f"Repaired {name} at ({agent.position.x}, {agent.position.y})", importance=0.6))
                    build_succeeded = True  # reuse flag for bus event
                    await self.bus.emit(BusEvent(
                        type=BusEventType.STRUCTURE_REPAIRED,
                        tick=tick,
                        agent_id=agent.id,
                        data={
                            "structure_type": repaired.structure_type.value,
                            "custom_name": repaired.custom_name,
                            "position": {"x": agent.position.x, "y": agent.position.y},
                            "health": repaired.health,
                        },
                    ))
                else:
                    feedback = "No damaged structures here to repair."

        elif action.type == ActionType.WAIT:
            pass  # Nothing to do

        return feedback, build_succeeded

    def _execute_move(
        self,
        agent: AgentState,
        action: Action,
        world: World,
    ) -> None:
        """Move the agent in the specified direction, respecting terrain and path effects."""
        if action.direction is None:
            return

        dx, dy = action.direction
        new_x = agent.position.x + dx
        new_y = agent.position.y + dy

        # Bounds check
        if not world.in_bounds(new_x, new_y):
            return

        # Terrain movement cost (with path structure bonus)
        target_tile = world.get_tile(new_x, new_y)
        if target_tile is None:
            return

        terrain_name = target_tile.terrain.value
        base_cost = self.config.movement_cost.get(terrain_name, 1)
        path_mult = get_path_cost_multiplier(target_tile, self.config)
        cost = base_cost * path_mult

        move_bonus = get_efficiency_bonus(agent, "move", self.config)
        effective_speed = agent.capabilities.movement_speed * move_bonus
        if effective_speed / cost >= 1.0:
            agent.position = Position(new_x, new_y)
        else:
            # Probabilistic movement
            if self._rng.random() < (effective_speed / cost):
                agent.position = Position(new_x, new_y)

    def _execute_gather(
        self,
        agent: AgentState,
        action: Action,
        world: World,
    ) -> None:
        """Gather a resource from the current tile into inventory.

        Resources go to inventory, not directly to needs. Also checks
        storage structures if tile resources are depleted.
        Specialisation bonus: gathering specialists deplete more efficiently.
        """
        if action.resource_type is None:
            return

        # Check inventory capacity
        if len(agent.inventory) >= self.config.agent_carry_capacity:
            logger.debug(
                "Agent %d inventory full, cannot gather", agent.id,
            )
            return

        # Specialisation bonus: gathering specialists extract more
        bonus = get_efficiency_bonus(agent, "gather", self.config)
        # Innovation structure bonus: boost_gathering structures on tile
        tile = world.get_tile(agent.position.x, agent.position.y)
        struct_bonus = get_gathering_bonus(tile) if tile else 1.0
        effective_rate = self.config.resource_depletion_rate * bonus * struct_bonus

        # Try natural tile resources first
        depleted = world.deplete_resource(
            agent.position,
            action.resource_type,
            effective_rate,
        )

        if depleted > 0:
            agent.inventory.append(action.resource_type)
            # Record gathering pressure for environmental co-evolution
            from src.engine.feedback import record_gathering_pressure
            tile = world.get_tile(agent.position.x, agent.position.y)
            if tile is not None:
                record_gathering_pressure(tile, action.resource_type, depleted)
            logger.debug(
                "Agent %d gathered %s -> inventory (%d/%d)",
                agent.id, action.resource_type,
                len(agent.inventory), self.config.agent_carry_capacity,
            )
            return

        # Try storage structures on the tile
        from src.engine.structures import retrieve_from_storage
        tile = world.get_tile(agent.position.x, agent.position.y)
        if tile is not None and retrieve_from_storage(tile, action.resource_type):
            agent.inventory.append(action.resource_type)
            logger.debug(
                "Agent %d took %s from storage -> inventory",
                agent.id, action.resource_type,
            )

    def _execute_communicate(
        self,
        agent: AgentState,
        action: Action,
        world_state: WorldState,
    ) -> None:
        """Send a message from agent to target (or broadcast)."""
        if action.message is None:
            return

        target_id = action.target_agent_id
        config = self.config
        tick = world_state.tick

        if target_id is not None and target_id == -1:
            # Broadcast to all agents in communication range
            nearby = self._get_agents_in_comm_range(agent, world_state)
            for other in nearby:
                self._deliver_message(agent, other, action.message, world_state)
        elif target_id is not None and target_id in world_state.agents:
            # Direct message to specific agent
            target = world_state.agents[target_id]
            comm_bonus = get_efficiency_bonus(agent, "communicate", self.config)
            effective_range = config.agent_communication_range * comm_bonus
            if agent.position.distance_to(target.position) <= effective_range:
                self._deliver_message(agent, target, action.message, world_state)
        else:
            # No valid target — broadcast
            nearby = self._get_agents_in_comm_range(agent, world_state)
            for other in nearby:
                self._deliver_message(agent, other, action.message, world_state)

    def _execute_build(
        self,
        agent: AgentState,
        action: Action,
        world: World,
        world_state: WorldState,
    ) -> bool:
        """Build a structure on the agent's current tile. Returns True if successful."""
        stype = action.structure_type
        if stype is None:
            return False

        tile = world.get_tile(agent.position.x, agent.position.y)
        if tile is None:
            return False

        # Try base structure types first (shelter, storage, marker, path)
        structure = build_structure(
            agent, stype, tile, self.config, world_state.tick,
            message=action.marker_message,
        )
        # build_structure returns None if requirements not met
        if structure is not None:
            agent.structures_built_count += 1
            memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
            memory_store.add(MemoryEntry(tick=world_state.tick, summary=f"Built a {stype} at ({agent.position.x}, {agent.position.y})", importance=0.8))
            return True

        # Try innovated/composed structure types (from discovered recipes)
        from src.agents.innovation import build_innovation
        for recipe in world_state.discovered_recipes:
            if recipe.output_name.lower().replace(" ", "_") == stype.lower().replace(" ", "_"):
                inno_structure = build_innovation(agent, recipe, tile, world_state)
                if inno_structure is not None:
                    agent.structures_built_count += 1
                    memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
                    memory_store.add(MemoryEntry(
                        tick=world_state.tick,
                        summary=f"Built {recipe.output_name} at ({agent.position.x}, {agent.position.y}): {recipe.output_description}",
                        importance=0.9,
                    ))
                    return True
                break  # Found the recipe but lacked resources

        return False

    def _execute_consume(
        self,
        agent: AgentState,
        action: Action,
    ) -> bool:
        """Consume a resource from inventory to satisfy the corresponding need. Returns True if successful."""
        rtype = action.resource_type
        if rtype is None:
            return False

        if rtype in agent.inventory:
            agent.inventory.remove(rtype)
            agent.needs.satisfy(rtype, self.config.agent_gather_restore)
            logger.debug(
                "Agent %d consumed %s, %s need now %.2f",
                agent.id, rtype, rtype, agent.needs.levels.get(rtype, 0),
            )
            return True
        return False

    def _execute_store(
        self,
        agent: AgentState,
        action: Action,
        world: World,
    ) -> None:
        """Store a held resource into a storage structure on the current tile."""
        rtype = action.resource_type
        if rtype is None:
            return

        tile = world.get_tile(agent.position.x, agent.position.y)
        if tile is None:
            return

        store_resource(agent, tile, rtype)

    def _execute_read_marker(
        self,
        agent: AgentState,
        action: Action,
        world: World,
        world_state: WorldState,
    ) -> None:
        """Read marker messages on the current tile."""
        tile = world.get_tile(agent.position.x, agent.position.y)
        if tile is None:
            return

        markers = read_marker(tile)
        memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
        for builder_id, message in markers:
            memory_store.add(MemoryEntry(
                tick=world_state.tick,
                summary=f"Read marker from Entity {builder_id}: {message}",
                importance=0.7,
            ))

    # ------------------------------------------------------------------
    # Resource transfer (GIVE)
    # ------------------------------------------------------------------

    def _execute_give(
        self,
        agent: AgentState,
        action: Action,
        world_state: WorldState,
    ) -> str:
        """Transfer a resource from agent's inventory to a nearby agent.

        Returns empty string on success, feedback string on failure.
        """
        resource = action.resource_type
        target_id = action.target_agent_id

        if resource is None or target_id is None:
            return "You tried to give something but the target or resource wasn't clear."

        if target_id not in world_state.agents:
            return f"Entity {target_id} doesn't exist."

        target = world_state.agents[target_id]

        # Must be within communication range
        comm_range = self.config.agent_communication_range
        if agent.position.distance_to(target.position) > comm_range:
            return f"Entity {target_id} is too far away. Move closer first."

        if resource not in agent.inventory:
            inv_str = ", ".join(agent.inventory) if agent.inventory else "empty"
            return f"You don't have {resource} in your inventory. Carrying: {inv_str}."

        if len(target.inventory) >= self.config.agent_carry_capacity:
            return f"Entity {target_id}'s inventory is full — they can't carry more."

        # Transfer the resource
        agent.inventory.remove(resource)
        target.inventory.append(resource)

        # Memory for the receiver
        target_ms = MemoryStore(target.memories, target.capabilities.memory_capacity)
        target_ms.add(MemoryEntry(
            tick=world_state.tick,
            summary=f"Received {resource} from Entity {agent.id}",
            importance=0.7,
        ))

        # Relationship boost for both parties
        if target_id not in agent.relationships:
            agent.relationships[target_id] = RelationshipRecord()
        agent.relationships[target_id].interaction_count += 1
        agent.relationships[target_id].positive_count += 1
        agent.relationships[target_id].last_interaction_tick = world_state.tick

        if agent.id not in target.relationships:
            target.relationships[agent.id] = RelationshipRecord()
        target.relationships[agent.id].interaction_count += 1
        target.relationships[agent.id].positive_count += 1
        target.relationships[agent.id].last_interaction_tick = world_state.tick

        return ""  # success

    # ------------------------------------------------------------------
    # Collective rules execution
    # ------------------------------------------------------------------

    async def _execute_propose_rule(
        self,
        agent: AgentState,
        action: Action,
        world_state: WorldState,
    ) -> None:
        """Propose a new collective rule."""
        if not self.config.enable_collective_rules or not action.rule_text:
            return

        from src.types import CollectiveRule
        rule = CollectiveRule(
            rule_id=world_state.next_rule_id,
            text=action.rule_text,
            proposed_by=agent.id,
            proposed_tick=world_state.tick,
            accepted_by=[agent.id],  # proposer implicitly accepts
        )
        world_state.collective_rules.append(rule)
        world_state.next_rule_id += 1

        await self.bus.emit(BusEvent(
            type=BusEventType.RULE_PROPOSED,
            tick=world_state.tick,
            agent_id=agent.id,
            data={"rule_id": rule.rule_id, "text": rule.text},
        ))
        # Record rule proposal as memory
        memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
        memory_store.add(MemoryEntry(
            tick=world_state.tick,
            summary=f"Proposed collective rule: \"{rule.text}\"",
            importance=0.8,
        ))

    async def _execute_accept_rule(
        self,
        agent: AgentState,
        action: Action,
        world_state: WorldState,
    ) -> None:
        """Accept a proposed collective rule."""
        if not self.config.enable_collective_rules or action.rule_id is None:
            return

        rule = self._find_rule(action.rule_id, world_state)
        if rule is None:
            return

        if agent.id not in rule.accepted_by and agent.id not in rule.ignored_by:
            rule.accepted_by.append(agent.id)

            await self.bus.emit(BusEvent(
                type=BusEventType.RULE_ACCEPTED,
                tick=world_state.tick,
                agent_id=agent.id,
                data={"rule_id": rule.rule_id, "adoption_rate": rule.adoption_rate},
            ))
            # Record acceptance as memory
            memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
            memory_store.add(MemoryEntry(
                tick=world_state.tick,
                summary=f"Accepted rule #{rule.rule_id}: \"{rule.text}\"",
                importance=0.6,
            ))

            # Check if rule just became established
            if not rule.established and rule.adoption_rate >= self.config.rule_establishment_threshold:
                rule.established = True
                # Credit the proposer
                proposer = world_state.agents.get(rule.proposed_by)
                if proposer is not None:
                    proposer.rules_established_count += 1
                await self.bus.emit(BusEvent(
                    type=BusEventType.RULE_ESTABLISHED,
                    tick=world_state.tick,
                    agent_id=agent.id,
                    data={
                        "rule_id": rule.rule_id,
                        "text": rule.text,
                        "adoption_rate": rule.adoption_rate,
                    },
                ))

    async def _execute_ignore_rule(
        self,
        agent: AgentState,
        action: Action,
        world_state: WorldState,
    ) -> None:
        """Explicitly ignore a proposed collective rule."""
        if not self.config.enable_collective_rules or action.rule_id is None:
            return

        rule = self._find_rule(action.rule_id, world_state)
        if rule is None:
            return

        if agent.id not in rule.accepted_by and agent.id not in rule.ignored_by:
            rule.ignored_by.append(agent.id)

    def _find_rule(self, rule_id: int, world_state: WorldState) -> Any:
        """Find a collective rule by ID."""
        for rule in world_state.collective_rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    # ------------------------------------------------------------------
    # Composition execution
    # ------------------------------------------------------------------

    async def _execute_compose(
        self,
        agent: AgentState,
        action: Action,
        world: World,
        world_state: WorldState,
    ) -> None:
        """Attempt to compose structures on the current tile."""
        if not self.config.enable_composition or not action.compose_targets:
            return

        from src.engine.composition import attempt_composition
        result = await attempt_composition(
            agent=agent,
            targets=action.compose_targets,
            world=world,
            world_state=world_state,
            config=self.config,
            llm_client=self.llm_client,
        )

        if result is not None:
            recipe_name, description = result
            await self.bus.emit(BusEvent(
                type=BusEventType.COMPOSITION_DISCOVERED,
                tick=world_state.tick,
                agent_id=agent.id,
                data={
                    "inputs": action.compose_targets,
                    "output_name": recipe_name,
                    "description": description,
                },
            ))
            # Record composition as memory
            memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
            memory_store.add(MemoryEntry(
                tick=world_state.tick,
                summary=f"Combined {' + '.join(action.compose_targets)} to create {recipe_name}: {description}",
                importance=0.9,
            ))
        else:
            await self.bus.emit(BusEvent(
                type=BusEventType.COMPOSITION_FAILED,
                tick=world_state.tick,
                agent_id=agent.id,
                data={"inputs": action.compose_targets},
            ))
            # Record failed attempt as memory
            memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
            memory_store.add(MemoryEntry(
                tick=world_state.tick,
                summary=f"Tried to combine {' + '.join(action.compose_targets)} but it didn't work.",
                importance=0.5,
            ))

    # ------------------------------------------------------------------
    # Innovation execution
    # ------------------------------------------------------------------

    async def _execute_propose_innovation(
        self,
        agent: AgentState,
        action: Action,
        world: World,
        world_state: WorldState,
    ) -> None:
        """Propose and evaluate an entirely new structure type."""
        if not self.config.enable_innovation or not action.innovation_description:
            return

        from src.agents.innovation import evaluate_innovation, register_innovation
        result = await evaluate_innovation(
            agent=agent,
            description=action.innovation_description,
            world=world,
            world_state=world_state,
            config=self.config,
            llm_client=self.llm_client,
        )

        if result is not None:
            name, effect_desc, recipe, effect_type = result
            # Register as a discoverable recipe with mechanical effect
            register_innovation(agent, name, effect_desc, recipe, world_state, effect_type=effect_type)
            agent.innovations_proposed.append(name)

            await self.bus.emit(BusEvent(
                type=BusEventType.INNOVATION_SUCCEEDED,
                tick=world_state.tick,
                agent_id=agent.id,
                data={
                    "name": name,
                    "description": effect_desc,
                    "recipe": recipe,
                },
            ))

            # Record as memory
            memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
            memory_store.add(MemoryEntry(
                tick=world_state.tick,
                summary=f"Invented {name}: {effect_desc}. Requires: {', '.join(recipe)}.",
                importance=0.9,
            ))
        else:
            await self.bus.emit(BusEvent(
                type=BusEventType.INNOVATION_FAILED,
                tick=world_state.tick,
                agent_id=agent.id,
                data={"description": action.innovation_description},
            ))
            # Record failed innovation as memory
            memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
            memory_store.add(MemoryEntry(
                tick=world_state.tick,
                summary=f"Proposed innovation '{action.innovation_description}' but it wasn't feasible.",
                importance=0.6,
            ))

    def _get_agents_in_comm_range(
        self,
        agent: AgentState,
        world_state: WorldState,
    ) -> list[AgentState]:
        """Return agents within communication range."""
        result: list[AgentState] = []
        for other in world_state.agents.values():
            if other.id == agent.id:
                continue
            comm_bonus = get_efficiency_bonus(agent, "communicate", self.config)
            effective_range = self.config.agent_communication_range * comm_bonus
            if agent.position.distance_to(other.position) <= effective_range:
                result.append(other)
        return result

    def _deliver_message(
        self,
        sender: AgentState,
        receiver: AgentState,
        content: str,
        world_state: WorldState,
    ) -> None:
        """Deliver a message and record the interaction for wellbeing bonuses."""
        tick = world_state.tick
        msg = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            content=content,
            tick=tick,
        )
        world_state.messages_this_tick.append(msg)

        # Track interactions for wellbeing bonuses
        if receiver.id not in sender.interactions_this_tick:
            sender.interactions_this_tick.append(receiver.id)
        if sender.id not in receiver.interactions_this_tick:
            receiver.interactions_this_tick.append(sender.id)

        truncated_msg = content[:300] if len(content) > 300 else content

        # Record memory of this communication for the sender
        sender_memory = MemoryStore(sender.memories, sender.capabilities.memory_capacity)
        sender_memory.record_interaction(receiver.id, truncated_msg, tick)

        # Update sender's relationship with receiver
        if receiver.id not in sender.relationships:
            sender.relationships[receiver.id] = RelationshipRecord()
        s_rel = sender.relationships[receiver.id]
        s_rel.interaction_count += 1
        s_rel.positive_count += 1  # communication is inherently positive
        s_rel.last_interaction_tick = tick
        if s_rel.positive_count >= self.config.agent_bond_threshold and not s_rel.is_bonded:
            s_rel.is_bonded = True

        # Record memory of this communication for the receiver
        receiver_memory = MemoryStore(receiver.memories, receiver.capabilities.memory_capacity)
        receiver_memory.record_interaction(sender.id, truncated_msg, tick)

        # Update receiver's relationship with sender
        if sender.id not in receiver.relationships:
            receiver.relationships[sender.id] = RelationshipRecord()
        r_rel = receiver.relationships[sender.id]
        r_rel.interaction_count += 1
        r_rel.positive_count += 1
        r_rel.last_interaction_tick = tick
        if r_rel.positive_count >= self.config.agent_bond_threshold and not r_rel.is_bonded:
            r_rel.is_bonded = True

        # Emit MESSAGE_SENT to event bus (powers watcher communication stats)
        self.bus.emit_sync(BusEvent(
            type=BusEventType.MESSAGE_SENT,
            tick=tick,
            agent_id=sender.id,
            data={
                "sender_id": sender.id,
                "receiver_id": receiver.id,
                "content": content[:500],
            },
        ))

        # Teaching: master-level specialists transfer skill XP when communicating
        taught = apply_teaching(sender, receiver, self.config)
        if taught:
            teach_ms = MemoryStore(receiver.memories, receiver.capabilities.memory_capacity)
            teach_ms.add(MemoryEntry(
                tick=tick,
                summary=f"Learned {taught} from Entity {sender.id}",
                importance=0.8,
            ))

        # Fire RECEIVED_MESSAGE event on receiver — they'll receive it as
        # a trigger for their agentic turn (same tick if they haven't gone
        # yet, otherwise next tick).
        from src.types import Event, EventType
        recv_event = Event(
            type=EventType.RECEIVED_MESSAGE,
            tick=tick,
            agent_id=receiver.id,
            data={
                "sender_id": sender.id,
                "content": content,
            },
        )
        world_state.events_this_tick.append(recv_event)

        logger.debug(
            "Agent %d -> Agent %d: '%s'",
            sender.id, receiver.id, content[:60],
        )

    # ------------------------------------------------------------------
    # Observation (re-perceive after action)
    # ------------------------------------------------------------------

    def _observe(
        self,
        agent: AgentState,
        action: Action,
        world: World,
        world_state: WorldState,
        action_feedback: str = "",
    ) -> str:
        """Re-perceive the world after an action and return a text description.

        The observation tells the agent what changed as a result of their action.
        """
        # Re-run perception
        vis_res = visible_resources(
            agent.position,
            agent.capabilities.perception_range,
            world.tiles,
        )
        vis_agents_list = visible_agents(agent, world_state.agents)

        # Build observation text based on what action was taken
        parts: list[str] = []

        if action.type == ActionType.MOVE:
            if action_feedback:
                parts.append(action_feedback)
            elif action.direction:
                dir_name = _direction_name(action.direction)
                parts.append(f"You moved {dir_name}. You are now at [{agent.position.x}, {agent.position.y}].")
            else:
                parts.append(f"You are at [{agent.position.x}, {agent.position.y}].")

        elif action.type == ActionType.GATHER:
            if action_feedback:
                parts.append(action_feedback)
            else:
                rtype = action.resource_type or "unknown"
                parts.append(f"You gathered {rtype} into your inventory. Carrying: {', '.join(agent.inventory)} ({len(agent.inventory)}/{self.config.agent_carry_capacity}).")

        elif action.type == ActionType.CONSUME:
            if action_feedback:
                parts.append(action_feedback)
            else:
                rtype = action.resource_type or "unknown"
                need_level = agent.needs.levels.get(rtype, 0)
                parts.append(f"You consumed {rtype}. Your {rtype} need is now {need_level:.2f}. Carrying: {', '.join(agent.inventory) or 'nothing'}.")

        elif action.type == ActionType.BUILD:
            if action_feedback:
                parts.append(action_feedback)
            else:
                stype = action.structure_type or "unknown"
                parts.append(f"You built a {stype} at [{agent.position.x}, {agent.position.y}]. Remaining inventory: {', '.join(agent.inventory) or 'empty'}.")

        elif action.type == ActionType.STORE:
            rtype = action.resource_type or "unknown"
            parts.append(f"You stored {rtype} in a storage structure. Carrying: {', '.join(agent.inventory) or 'nothing'}.")

        elif action.type == ActionType.READ_MARKER:
            tile = world.get_tile(agent.position.x, agent.position.y)
            if tile:
                markers = read_marker(tile)
                if markers:
                    for builder_id, message in markers[:3]:
                        parts.append(f'Marker from Entity {builder_id}: "{message}"')
                else:
                    parts.append("No readable markers here.")
            else:
                parts.append("No markers here.")

        elif action.type == ActionType.COMMUNICATE:
            parts.append(f"You sent a message.")

        elif action.type == ActionType.COMPOSE:
            targets = action.compose_targets or []
            parts.append(f"You attempted to compose {' + '.join(targets)}.")

        elif action.type == ActionType.PROPOSE_INNOVATION:
            desc = action.innovation_description or "unknown"
            parts.append(f"You proposed an innovation: {desc}.")

        elif action.type == ActionType.PROPOSE_RULE:
            text = action.rule_text or "unknown"
            parts.append(f"You proposed a rule: \"{text}\".")

        elif action.type == ActionType.ACCEPT_RULE:
            parts.append(f"You accepted rule #{action.rule_id}.")

        elif action.type == ActionType.IGNORE_RULE:
            parts.append(f"You ignored rule #{action.rule_id}.")

        elif action.type == ActionType.GIVE:
            if action_feedback:
                parts.append(action_feedback)
            else:
                rtype = action.resource_type or "resource"
                target = action.target_agent_id
                inv_str = ", ".join(agent.inventory) if agent.inventory else "nothing"
                parts.append(f"You gave {rtype} to Entity {target}. Carrying: {inv_str}.")

        elif action.type == ActionType.REPAIR:
            if action_feedback:
                parts.append(action_feedback)
            else:
                parts.append(f"You repaired a structure. Remaining inventory: {', '.join(agent.inventory) or 'empty'}.")

        elif action.type == ActionType.WAIT:
            parts.append("You waited.")

        # Describe what's visible now — distinguish on-tile from nearby
        res_here: list[str] = []
        res_nearby: list[str] = []
        for pos, res in vis_res:
            label = f"{res.resource_type} ({res.amount:.2f}) at [{pos.x}, {pos.y}]"
            if pos.x == agent.position.x and pos.y == agent.position.y:
                res_here.append(label)
            else:
                res_nearby.append(label)
        if res_here:
            parts.append(f"ON YOUR TILE (gatherable): {', '.join(res_here[:5])}.")
        if res_nearby:
            parts.append(f"NEARBY (move there first): {', '.join(res_nearby[:5])}.")
        if not res_here and not res_nearby:
            parts.append("No resources visible nearby.")

        # Describe visible structures
        tile = world.get_tile(agent.position.x, agent.position.y)
        if tile and tile.structures:
            struct_descs = describe_structures(tile)
            if struct_descs:
                parts.append(f"Structures here: {'; '.join(struct_descs[:3])}.")

        if vis_agents_list:
            agent_strs = [f"Entity {a.id} at [{a.position.x}, {a.position.y}]" for a in vis_agents_list[:5]]
            parts.append(f"Nearby entities: {', '.join(agent_strs)}.")

        # Note critical needs
        if agent.needs.any_critical():
            lowest_type, lowest_val = agent.needs.lowest()
            parts.append(f"Warning: your {lowest_type} need is critically low ({lowest_val:.2f}).")

        return " ".join(parts)

    # ------------------------------------------------------------------
    # Goal and plan management
    # ------------------------------------------------------------------

    def _apply_goal(self, agent: AgentState, action: Action) -> None:
        """Apply a SET_GOAL action to the agent's state.

        Replaces an existing goal about the same topic, or appends if new.
        Keeps goals list short (max 3 active goals).
        """
        new_goal = action.goal
        if not new_goal:
            return

        # Simple topic matching: if any existing goal shares 2+ words
        # with the new goal, replace it
        new_words = set(new_goal.lower().split())
        replaced = False
        for i, existing in enumerate(agent.goals):
            existing_words = set(existing.lower().split())
            overlap = new_words & existing_words
            if len(overlap) >= 2:
                agent.goals[i] = new_goal
                replaced = True
                break

        if not replaced:
            agent.goals.append(new_goal)

        # Keep at most 3 active goals
        if len(agent.goals) > 3:
            agent.goals = agent.goals[-3:]

    def _apply_plan(self, agent: AgentState, action: Action) -> None:
        """Apply an UPDATE_PLAN action to the agent's state."""
        if action.plan_steps:
            agent.plan = list(action.plan_steps)


# ======================================================================
# Utility
# ======================================================================

def _direction_name(direction: tuple[int, int]) -> str:
    """Convert a (dx, dy) tuple to a human-readable direction name."""
    dx, dy = direction
    for name, (ndx, ndy) in _DIRECTION_MAP.items():
        if ndx == dx and ndy == dy:
            return name
    return f"({dx}, {dy})"
