"""Decision module for Agent Civilisation.

Two decision paths:
  PATH A — Deterministic (no LLM, cheap): used between agentic turns and when
           no events trigger. Now plan-aware: if the agent has plan steps,
           it executes the next step deterministically.
  PATH B — LLM-backed (called by the agentic loop): builds a prompt, parses
           the free-text response into a structured Action.

This module does NOT make the LLM API call itself — it builds prompts and
parses responses. The agentic loop handles the actual call.
"""

from __future__ import annotations

import random
import re
from typing import Optional

from src.config import SimulationConfig
from src.types import (
    Action,
    ActionType,
    AgentState,
    Capabilities,
    Event,
    Position,
    Resource,
    Tile,
)


# ---------------------------------------------------------------------------
# PATH A — Deterministic fallback (plan-aware)
# ---------------------------------------------------------------------------

def deterministic_action(
    agent: AgentState,
    vis_agents: list[AgentState],
    vis_resources: list[tuple[Position, Resource]],
    config: SimulationConfig,
) -> Action:
    """Choose an action without an LLM call.

    Priority:
      0. If agent has plan steps, parse and execute the first step.
      1. If any need is low, move toward nearest KNOWN resource of that type.
      2. If standing on a tile with a needed resource, gather it.
      3. If no known resources for the urgent need, explore (random walk biased
         away from recently visited positions).
      4. If wellbeing is high and no urgent needs, wander toward nearby agents
         (social pull).
    """
    # --- Plan-aware: execute next plan step if available ---
    if agent.plan:
        step = agent.plan[0]
        action = _parse_plan_step(step, agent, vis_agents, vis_resources)
        if action is not None:
            # Pop the step we just executed
            agent.plan.pop(0)
            return action
        # If the plan step couldn't be parsed into an action, fall through
        # to survival behavior and leave the step for the agentic loop.

    needs = agent.needs
    threshold = Capabilities.DEGRADATION_THRESHOLD

    # Find the most urgent need
    urgent_type, urgent_level = needs.lowest()

    # --- Gather if standing on a needed resource ---
    if urgent_level < 0.8:  # gather when somewhat depleted, not just critical
        for pos, res in vis_resources:
            if pos == agent.position and res.resource_type == urgent_type and res.amount > 0:
                return Action(
                    type=ActionType.GATHER,
                    resource_type=urgent_type,
                    reasoning="Gathering nearby resource to satisfy need.",
                )

    # --- Move toward nearest known resource of the urgent type ---
    if urgent_level < 0.8 and agent.known_resources:
        best_pos: Optional[tuple[int, int]] = None
        best_dist = float("inf")
        for pos_tuple, rtype in agent.known_resources.items():
            if rtype == urgent_type:
                px, py = pos_tuple
                d = agent.position.distance_to(Position(px, py))
                if d < best_dist:
                    best_dist = d
                    best_pos = pos_tuple

        if best_pos is not None:
            dx = _sign(best_pos[0] - agent.position.x)
            dy = _sign(best_pos[1] - agent.position.y)
            return Action(
                type=ActionType.MOVE,
                direction=(dx, dy),
                reasoning=f"Moving toward known {urgent_type} resource.",
            )

    # --- Explore: move toward any visible resource we need ---
    if urgent_level < 0.8:
        for pos, res in vis_resources:
            if res.resource_type == urgent_type and res.amount > 0:
                dx = _sign(pos.x - agent.position.x)
                dy = _sign(pos.y - agent.position.y)
                return Action(
                    type=ActionType.MOVE,
                    direction=(dx, dy),
                    reasoning=f"Moving toward visible {urgent_type} resource.",
                )

    # --- Social pull: wander toward nearby agents if wellbeing is moderate ---
    if agent.wellbeing > 0.4 and vis_agents:
        closest = min(vis_agents, key=lambda a: agent.position.distance_to(a.position))
        if agent.position.distance_to(closest.position) > 1:
            dx = _sign(closest.position.x - agent.position.x)
            dy = _sign(closest.position.y - agent.position.y)
            return Action(
                type=ActionType.MOVE,
                direction=(dx, dy),
                reasoning="Wandering toward nearby entity.",
            )

    # --- Random exploration (biased away from current position) ---
    dx = random.choice([-1, 0, 1])
    dy = random.choice([-1, 0, 1])
    if dx == 0 and dy == 0:
        dx = random.choice([-1, 1])
    return Action(
        type=ActionType.MOVE,
        direction=(dx, dy),
        reasoning="Exploring.",
    )


def _parse_plan_step(
    step: str,
    agent: AgentState,
    vis_agents: list[AgentState],
    vis_resources: list[tuple[Position, Resource]],
) -> Optional[Action]:
    """Attempt to parse a plan step into a deterministic action.

    Returns None if the step is too complex for deterministic execution
    (e.g. requires LLM reasoning, communicating, or setting goals).
    """
    step_lower = step.strip().lower()

    # "gather <resource>"
    gather_match = re.match(r'gather\s+(\w+)', step_lower)
    if gather_match:
        resource = gather_match.group(1)
        return Action(
            type=ActionType.GATHER,
            resource_type=resource,
            reasoning=f"Plan step: {step}",
        )

    # "move <direction>"
    direction_map = _direction_map()
    move_match = re.match(
        r'move\s+(north(?:east|west)?|south(?:east|west)?|east|west|up|down|left|right)',
        step_lower,
    )
    if move_match:
        direction_name = move_match.group(1)
        direction = direction_map.get(direction_name, (0, 0))
        return Action(
            type=ActionType.MOVE,
            direction=direction,
            reasoning=f"Plan step: {step}",
        )

    # "move toward <resource>" — move toward the nearest visible resource of that type
    toward_match = re.match(r'move\s+toward\s+(\w+)', step_lower)
    if toward_match:
        target_type = toward_match.group(1)
        for pos, res in vis_resources:
            if res.resource_type == target_type and res.amount > 0:
                dx = _sign(pos.x - agent.position.x)
                dy = _sign(pos.y - agent.position.y)
                return Action(
                    type=ActionType.MOVE,
                    direction=(dx, dy),
                    reasoning=f"Plan step: {step}",
                )
        # Resource not visible — move in a random direction (explore for it)
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        if dx == 0 and dy == 0:
            dx = random.choice([-1, 1])
        return Action(
            type=ActionType.MOVE,
            direction=(dx, dy),
            reasoning=f"Plan step (exploring for {target_type}): {step}",
        )

    # "wait"
    if step_lower.startswith("wait"):
        return Action(
            type=ActionType.WAIT,
            reasoning=f"Plan step: {step}",
        )

    # Step is too complex for deterministic execution
    return None


# ---------------------------------------------------------------------------
# PATH B — LLM-backed decision
# ---------------------------------------------------------------------------

def build_world_view(
    agent: AgentState,
    vis_tiles: list[Tile],
    vis_resources: list[tuple[Position, Resource]],
    vis_agents: list[AgentState],
) -> dict:
    """Build a structured world-view dict that the prompt template consumes."""
    nearby_tiles = [
        {
            "position": (t.position.x, t.position.y),
            "terrain": t.terrain.value,
            "resources": {
                rtype: {"amount": round(r.amount, 2), "type": rtype}
                for rtype, r in t.resources.items()
                if r.amount > 0
            },
        }
        for t in vis_tiles
        if t.resources  # only include tiles with resources for brevity
    ]

    nearby_resources = [
        {"position": (p.x, p.y), "type": r.resource_type, "amount": round(r.amount, 2)}
        for p, r in vis_resources
    ]

    nearby_agents = [
        {"id": a.id, "position": (a.position.x, a.position.y)}
        for a in vis_agents
    ]

    # Include goals and plan in the world view for consumers
    return {
        "nearby_tiles": nearby_tiles,
        "nearby_resources": nearby_resources,
        "nearby_agents": nearby_agents,
        "goals": list(agent.goals),
        "plan": list(agent.plan),
    }


def build_prompt(
    agent: AgentState,
    events: list[Event],
    world_view: dict,
    memory_summary: str,
) -> str:
    """Build the LLM prompt for an agent decision.

    CRITICAL: The prompt contains NO human behavioural instructions — no names,
    no personalities, no social norms, no hints about cooperation or competition.
    Just state, perception, memory, goals, plan, and available actions.
    """
    needs_str = ", ".join(
        f"{k}: {v:.2f}" for k, v in agent.needs.levels.items()
    )
    caps = agent.capabilities

    # Format events as the triggering situation
    situation_lines = [e.summary() for e in events]
    situation_str = "\n".join(situation_lines) if situation_lines else "Routine moment."

    # Format available actions with directions
    # Support both key conventions: tick.py uses "visible_*", decision.py used "nearby_*"
    wv_agents = world_view.get("nearby_agents") or world_view.get("visible_agents") or []
    wv_resources = world_view.get("nearby_resources") or world_view.get("visible_resources") or []

    def _agent_pos(a: dict) -> str:
        if "position" in a:
            return str(a["position"])
        return f"({a.get('x', '?')}, {a.get('y', '?')})"

    def _resource_pos(r: dict) -> str:
        if "position" in r:
            return str(r["position"])
        return f"({r.get('x', '?')}, {r.get('y', '?')})"

    nearby_agents_str = (
        ", ".join(f"Agent {a['id']} at {_agent_pos(a)}" for a in wv_agents)
        if wv_agents
        else "none"
    )

    nearby_resources_str = (
        ", ".join(
            f"{r['type']} ({r['amount']}) at {_resource_pos(r)}"
            for r in wv_resources
        )
        if wv_resources
        else "none"
    )

    # Goals and plan
    goals_str = _format_goals(agent.goals)
    plan_str = _format_plan(agent.plan)

    prompt = f"""You exist in a world alongside other entities like you. You were not given a name, a role, or instructions on how to behave. What you do is up to you.

Think out loud — express your inner thoughts naturally, as if talking to yourself. What do you notice? What do you want? What worries you? What interests you? Be specific and personal.

YOUR STATE:
- Position: [{agent.position.x}, {agent.position.y}]
- Needs: [{needs_str}] (these are your survival resources — when they drop low, your capabilities degrade. Gather resources from nearby tiles, then consume them from your inventory to restore needs.)
- Social Wellbeing: {agent.wellbeing:.2f} (this reflects your social fulfilment — it increases when you interact with or stay near other entities, and decays when you are alone)
- Curiosity: {agent.curiosity:.2f} (your drive to explore and discover — increases from visiting new places, meeting new entities, building, and innovating. When low, your perception narrows.)
- Capabilities: perception range {caps.perception_range:.1f}, movement speed {caps.movement_speed:.1f}

WHAT YOU CAN PERCEIVE:
- Nearby entities: {nearby_agents_str}
- Nearby resources: {nearby_resources_str}

YOUR MEMORY:
{memory_summary}

YOUR GOALS: {goals_str}
YOUR PLAN:
{plan_str}

CURRENT SITUATION: {situation_str}

HOW THE WORLD WORKS:
- You can GATHER resources from tiles you stand on (e.g. "gather water"). This adds them to your inventory.
- You can CONSUME resources from your inventory to restore your needs (e.g. "consume food").
- You can BUILD structures on your tile if you have the right resources: shelter (water + material), storage (food + material), marker (material), path (material + material).
- You can COMMUNICATE with nearby entities — say anything you want.
- You can MOVE in any direction: north, south, east, west, northeast, northwest, southeast, southwest.
- You can SET_GOAL and UPDATE_PLAN to organise your thinking over time.
- You can COMPOSE two structures into something more advanced, or PROPOSE_INNOVATION to invent something entirely new.
- You can PROPOSE_RULE to suggest a norm for how entities should behave, or ACCEPT_RULE / IGNORE_RULE for rules others propose.

What are you thinking? What do you do next?"""

    return prompt


def parse_response(response_text: str) -> Action:
    """Parse the LLM's free-text response into a structured Action.

    Lenient parsing — LLMs give varied formats. We look for keywords:
      set_goal [text]         -> SET_GOAL
      update_plan [s1|s2|s3]  -> UPDATE_PLAN
      done / end turn         -> DONE
      move north/south/etc    -> MOVE
      gather water/food/etc   -> GATHER
      communicate [message]   -> COMMUNICATE
      wait                    -> WAIT

    Also extracts the reasoning (the full response text).
    """
    text = response_text.strip().lower()
    reasoning = response_text.strip()

    # --- Done / end turn ---
    done_match = re.search(r'\b(done|end\s+turn)\b', text)
    if done_match:
        return Action(
            type=ActionType.DONE,
            reasoning=reasoning,
        )

    # --- Propose rule ---
    rule_match = re.search(r'propose_rule\s+["\'\[]?(.+?)["\'\]]?\s*(?:\n|$)', text, re.IGNORECASE)
    if rule_match:
        return Action(
            type=ActionType.PROPOSE_RULE,
            rule_text=rule_match.group(1).strip().rstrip("."),
            reasoning=reasoning,
        )

    # --- Accept rule ---
    accept_match = re.search(r'accept_rule\s+#?(\d+)', text)
    if accept_match:
        return Action(
            type=ActionType.ACCEPT_RULE,
            rule_id=int(accept_match.group(1)),
            reasoning=reasoning,
        )

    # --- Ignore rule ---
    ignore_match = re.search(r'ignore_rule\s+#?(\d+)', text)
    if ignore_match:
        return Action(
            type=ActionType.IGNORE_RULE,
            rule_id=int(ignore_match.group(1)),
            reasoning=reasoning,
        )

    # --- Compose ---
    compose_match = re.search(r'compose\s+(\w+)\s*\+\s*(\w+)', text, re.IGNORECASE)
    if compose_match:
        targets = [compose_match.group(1), compose_match.group(2)]
        return Action(
            type=ActionType.COMPOSE,
            compose_targets=sorted(targets),
            reasoning=reasoning,
        )

    # --- Propose innovation ---
    innovation_match = re.search(r'propose_innovation\s+["\'\[]?(.+?)["\'\]]?\s*(?:\n|$)', text, re.IGNORECASE)
    if innovation_match:
        return Action(
            type=ActionType.PROPOSE_INNOVATION,
            innovation_description=innovation_match.group(1).strip().rstrip("."),
            reasoning=reasoning,
        )

    # --- Build ---
    build_match = re.search(r'build\s+(\w+)(?:\s+["\'](.+?)["\'])?', text)
    if build_match:
        structure_type = build_match.group(1)
        marker_msg = build_match.group(2) if build_match.lastindex and build_match.lastindex >= 2 else None
        return Action(
            type=ActionType.BUILD,
            structure_type=structure_type,
            marker_message=marker_msg,
            reasoning=reasoning,
        )

    # --- Consume ---
    consume_match = re.search(r'consume\s+(\w+)', text)
    if consume_match:
        return Action(
            type=ActionType.CONSUME,
            resource_type=consume_match.group(1),
            reasoning=reasoning,
        )

    # --- Store ---
    store_match = re.search(r'store\s+(\w+)', text)
    if store_match:
        return Action(
            type=ActionType.STORE,
            resource_type=store_match.group(1),
            reasoning=reasoning,
        )

    # --- Read marker ---
    if re.search(r'\bread_marker\b', text) or re.search(r'\bread\s+marker\b', text):
        return Action(
            type=ActionType.READ_MARKER,
            reasoning=reasoning,
        )

    # --- Set goal ---
    goal_match = re.search(r'set_goal\s+(.+?)(?:\n|$)', text)
    if goal_match:
        goal_text = goal_match.group(1).strip().strip('"\'[]')
        return Action(
            type=ActionType.SET_GOAL,
            goal=goal_text,
            reasoning=reasoning,
        )

    # --- Update plan ---
    plan_match = re.search(r'update_plan\s+(.+?)(?:\n|$)', text)
    if plan_match:
        plan_raw = plan_match.group(1).strip().strip('[]')
        steps = [s.strip().strip('"\'') for s in plan_raw.split("|") if s.strip()]
        return Action(
            type=ActionType.UPDATE_PLAN,
            plan_steps=steps,
            reasoning=reasoning,
        )

    # --- Communicate ---
    comm_match = re.search(
        r'communicate\s+["\']?(.+?)["\']?\s*(?:to\s+(?:agent\s*)?(\d+))?',
        text,
        re.IGNORECASE,
    )
    if comm_match:
        message = comm_match.group(1).strip().rstrip(".")
        target_str = comm_match.group(2)
        target_id = int(target_str) if target_str else -1
        return Action(
            type=ActionType.COMMUNICATE,
            message=message,
            target_agent_id=target_id,
            reasoning=reasoning,
        )

    # Also catch "say", "tell", "send message" style phrasings
    say_match = re.search(
        r'(?:say|tell|send\s+message)\s+["\']?(.+?)["\']?\s*(?:to\s+(?:agent\s*)?(\d+))?',
        text,
        re.IGNORECASE,
    )
    if say_match:
        message = say_match.group(1).strip().rstrip(".")
        target_str = say_match.group(2)
        target_id = int(target_str) if target_str else -1
        return Action(
            type=ActionType.COMMUNICATE,
            message=message,
            target_agent_id=target_id,
            reasoning=reasoning,
        )

    # --- Gather ---
    gather_match = re.search(r'gather\s+(\w+)', text)
    if gather_match:
        resource = gather_match.group(1)
        return Action(
            type=ActionType.GATHER,
            resource_type=resource,
            reasoning=reasoning,
        )

    # --- Move ---
    direction_map = _direction_map()

    move_match = re.search(
        r'move\s+(north(?:east|west)?|south(?:east|west)?|east|west|up|down|left|right)',
        text,
    )
    if move_match:
        direction_name = move_match.group(1)
        direction = direction_map.get(direction_name, (0, 0))
        return Action(
            type=ActionType.MOVE,
            direction=direction,
            reasoning=reasoning,
        )

    # --- Wait ---
    if "wait" in text or "observe" in text or "stay" in text:
        return Action(
            type=ActionType.WAIT,
            reasoning=reasoning,
        )

    # --- Fallback: if no action parsed, default to wait ---
    return Action(
        type=ActionType.WAIT,
        reasoning=reasoning,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _direction_map() -> dict[str, tuple[int, int]]:
    return {
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
    """Return -1, 0, or 1."""
    if n > 0:
        return 1
    elif n < 0:
        return -1
    return 0


def _format_goals(goals: list[str]) -> str:
    """Format goals for the LLM prompt."""
    if not goals:
        return "none yet"
    return ", ".join(f"{i + 1}. {g}" for i, g in enumerate(goals))


def _format_plan(plan: list[str]) -> str:
    """Format plan steps for the LLM prompt."""
    if not plan:
        return "none yet"
    lines = []
    for i, step in enumerate(plan):
        marker = ">>>" if i == 0 else "   "
        lines.append(f"{marker} {i + 1}. {step}")
    return "\n".join(lines)
