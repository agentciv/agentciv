#!/usr/bin/env python3
"""Entry point for Agent Civilisation.

Usage:
    python3 scripts/run.py                          # run with defaults
    python3 scripts/run.py --config config.yaml     # explicit config
    python3 scripts/run.py --ticks 100              # run for 100 ticks
    python3 scripts/run.py --fast                   # force fast mode
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
import time

# Ensure the project root is on sys.path so `src.*` imports resolve
# regardless of where the script is invoked from.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.config import SimulationConfig
from src.types import (
    BusEvent,
    BusEventType,
    EventBus,
    WorldState,
)
from src.engine.world import World
from src.engine.environment import generate_world
from src.engine.tick import TickEngine
from src.engine.persistence import load_state, save_state, save_tick_snapshot
from src.agents.llm import LLMClient
from src.watcher.chronicle import Chronicle
from src.watcher.watcher import Watcher
from src.metrics.emergence import compute_emergence
from src.metrics.run_record import SimulationRunRecord, build_agent_summary

# Graceful import of AgenticLoop — another agent is building it.
# If not available yet, we fall back to deterministic-only mode.
try:
    from src.agents.agentic_loop import AgenticLoop
    _AGENTIC_LOOP_AVAILABLE = True
except ImportError:
    AgenticLoop = None  # type: ignore[misc, assignment]
    _AGENTIC_LOOP_AVAILABLE = False


# ======================================================================
# ANSI colour codes for terminal output
# ======================================================================

_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_MAGENTA = "\033[35m"


# ======================================================================
# EventBus CLI subscriber
# ======================================================================

def _resource_pct(world_state: WorldState) -> dict[str, float]:
    """Compute average resource fullness across the grid."""
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for col in world_state.tiles:
        for tile in col:
            for rtype, res in tile.resources.items():
                totals[rtype] = totals.get(rtype, 0.0) + (res.amount / res.max_amount if res.max_amount > 0 else 0.0)
                counts[rtype] = counts.get(rtype, 0) + 1
    return {k: totals[k] / counts[k] if counts[k] > 0 else 0.0 for k in totals}


def _format_direction(direction: tuple[int, int] | None) -> str:
    """Convert a (dx, dy) tuple to a human-readable direction string."""
    if direction is None:
        return "?"
    dx, dy = direction
    names = {
        (0, -1): "north", (0, 1): "south", (1, 0): "east", (-1, 0): "west",
        (1, -1): "northeast", (-1, -1): "northwest",
        (1, 1): "southeast", (-1, 1): "southwest",
        (0, 0): "stayed",
    }
    return names.get((dx, dy), f"({dx},{dy})")


def make_cli_subscriber(config: SimulationConfig, world_state: WorldState):
    """Create a sync event bus subscriber that prints formatted CLI output.

    The subscriber is a plain function that receives BusEvent instances and
    prints them to stdout with appropriate formatting based on log level.
    """
    log_level = config.log_level.upper()

    def on_event(event: BusEvent) -> None:
        # --- WARNING level: only tick summaries ---
        if log_level == "WARNING":
            if event.type == BusEventType.TICK_END:
                data = event.data
                agents = world_state.agents
                num_agents = len(agents)
                degraded = sum(
                    1 for a in agents.values()
                    if (a.capabilities.perception_range < a.capabilities.base_perception_range
                        or a.capabilities.movement_speed < a.capabilities.base_movement_speed
                        or a.capabilities.memory_capacity < a.capabilities.base_memory_capacity)
                )
                avg_wb = sum(a.wellbeing for a in agents.values()) / num_agents if num_agents > 0 else 0.0
                res_pct = _resource_pct(world_state)
                res_str = " ".join(f"{k} {v:.0%}" for k, v in res_pct.items())
                degraded_str = f" ({degraded} degraded)" if degraded > 0 else ""
                print(
                    f"Tick {event.tick}: "
                    f"{num_agents} agents{degraded_str} | "
                    f"wb {avg_wb:.2f} | "
                    f"res: {res_str}"
                )
            return

        # --- INFO and DEBUG levels ---
        if event.type == BusEventType.TICK_START:
            agents = world_state.agents
            num_agents = len(agents)
            degraded = sum(
                1 for a in agents.values()
                if (a.capabilities.perception_range < a.capabilities.base_perception_range
                    or a.capabilities.movement_speed < a.capabilities.base_movement_speed
                    or a.capabilities.memory_capacity < a.capabilities.base_memory_capacity)
            )
            avg_wb = sum(a.wellbeing for a in agents.values()) / num_agents if num_agents > 0 else 0.0
            res_pct = _resource_pct(world_state)
            res_str = " ".join(f"{k} {v:.0%}" for k, v in res_pct.items())
            degraded_str = f" ({degraded} degraded)" if degraded > 0 else ""
            print(f"\n{_BOLD}{'=' * 3} Tick {event.tick} {'=' * 65}{_RESET}")
            print(
                f"Agents: {num_agents}{degraded_str} | "
                f"Avg wellbeing: {avg_wb:.2f} | "
                f"Resources: {res_str}"
            )

        elif event.type == BusEventType.AGENTIC_TURN_START:
            if log_level == "DEBUG":
                trigger = event.data.get("trigger", "")
                print(f"  {_CYAN}Agent {event.agent_id}{_RESET}: agentic turn started ({trigger})")

        elif event.type == BusEventType.REASONING_STEP:
            if config.show_agent_reasoning:
                response = event.data.get("response", "")
                truncated = response[:200]
                if len(response) > 200:
                    truncated += "..."
                print(f"    {_DIM}Agent {event.agent_id} thinks: {truncated}{_RESET}")

        elif event.type == BusEventType.ACTION_TAKEN:
            action_str = event.data.get("action", "?")
            reason = event.data.get("reasoning", "")
            truncated_reason = reason[:100]
            if len(reason) > 100:
                truncated_reason += "..."
            print(f"    {_GREEN}->{_RESET} {action_str}: {truncated_reason}")

        elif event.type == BusEventType.GOAL_SET:
            goal = event.data.get("goal", "")
            print(f"    {_YELLOW}* New goal: {goal}{_RESET}")

        elif event.type == BusEventType.GOAL_COMPLETED:
            goal = event.data.get("goal", "")
            print(f"    {_GREEN}* Goal completed: {goal}{_RESET}")

        elif event.type == BusEventType.PLAN_UPDATED:
            plan = event.data.get("plan", [])
            preview = " -> ".join(plan[:3])
            if len(plan) > 3:
                preview += f" ... ({len(plan)} total)"
            print(f"    Plan: {preview}")

        elif event.type == BusEventType.MESSAGE_SENT:
            if config.show_conversations:
                sender = event.data.get("sender_id", "?")
                receiver = event.data.get("receiver_id", "?")
                content = event.data.get("content", "")
                print(f"  {_MAGENTA}Agent {sender} -> Agent {receiver}:{_RESET} \"{content}\"")

        elif event.type == BusEventType.MESSAGE_RECEIVED:
            # Typically don't print receive side — the SENT event covers it.
            pass

        elif event.type == BusEventType.OBSERVATION:
            if log_level == "DEBUG":
                obs = event.data.get("observation", "")
                truncated = obs[:150]
                if len(obs) > 150:
                    truncated += "..."
                print(f"    {_DIM}Observed: {truncated}{_RESET}")

        elif event.type == BusEventType.DETERMINISTIC_ACTION:
            if log_level == "DEBUG":
                action_str = event.data.get("action", "?")
                reason = event.data.get("reasoning", "")
                print(f"    {_DIM}Agent {event.agent_id}: {action_str} ({reason}){_RESET}")

        elif event.type == BusEventType.AGENT_ARRIVED:
            aid = event.data.get("agent_id", "?")
            pos = event.data.get("position", "?")
            print(f"  {_CYAN}New agent {aid} arrived at {pos}{_RESET}")

        elif event.type == BusEventType.ENVIRONMENTAL_SHIFT:
            severity = event.data.get("severity", "?")
            print(f"  {_YELLOW}Environmental shift ({severity}){_RESET}")

        elif event.type == BusEventType.NEEDS_CRITICAL:
            if log_level == "DEBUG":
                need = event.data.get("need", "?")
                level = event.data.get("level", "?")
                print(f"    {_RED}Agent {event.agent_id}: {need} critical ({level}){_RESET}")

        elif event.type == BusEventType.STRUCTURE_BUILT:
            stype = event.data.get("structure_type", "?")
            pos = event.data.get("position", {})
            print(f"  {_YELLOW}Agent {event.agent_id} built {stype} at [{pos.get('x', '?')}, {pos.get('y', '?')}]{_RESET}")

        elif event.type == BusEventType.STRUCTURE_DECAYED:
            stype = event.data.get("structure_type", "?")
            pos = event.data.get("position", {})
            if log_level == "DEBUG":
                print(f"  {_DIM}Structure {stype} decayed at [{pos.get('x', '?')}, {pos.get('y', '?')}]{_RESET}")

        elif event.type == BusEventType.MARKER_READ:
            if log_level == "DEBUG":
                pos = event.data.get("position", {})
                print(f"    {_DIM}Agent {event.agent_id} read marker at [{pos.get('x', '?')}, {pos.get('y', '?')}]{_RESET}")

        elif event.type == BusEventType.RESOURCE_STORED:
            if log_level == "DEBUG":
                rtype = event.data.get("resource_type", "?")
                print(f"    {_DIM}Agent {event.agent_id} stored {rtype}{_RESET}")

        elif event.type == BusEventType.RESOURCE_CONSUMED:
            if log_level == "DEBUG":
                rtype = event.data.get("resource_type", "?")
                print(f"    {_DIM}Agent {event.agent_id} consumed {rtype}{_RESET}")

        # --- Composition & innovation ---
        elif event.type == BusEventType.COMPOSITION_DISCOVERED:
            output = event.data.get("output_name", "?")
            inputs = event.data.get("inputs", [])
            print(f"  {_YELLOW}Agent {event.agent_id} discovered composition: {' + '.join(inputs)} -> {output}{_RESET}")

        elif event.type == BusEventType.COMPOSITION_FAILED:
            inputs = event.data.get("inputs", [])
            if log_level == "DEBUG":
                print(f"    {_DIM}Composition failed: {' + '.join(inputs)}{_RESET}")

        elif event.type == BusEventType.INNOVATION_SUCCEEDED:
            name = event.data.get("name", "?")
            desc = event.data.get("description", "")[:80]
            print(f"  {_YELLOW}Agent {event.agent_id} innovated: {name} — {desc}{_RESET}")

        elif event.type == BusEventType.INNOVATION_FAILED:
            if log_level == "DEBUG":
                desc = event.data.get("description", "?")[:60]
                print(f"    {_DIM}Innovation rejected: {desc}{_RESET}")

        # --- Collective rules ---
        elif event.type == BusEventType.RULE_PROPOSED:
            text = event.data.get("text", "?")[:80]
            print(f"  {_MAGENTA}Agent {event.agent_id} proposed rule: \"{text}\"{_RESET}")

        elif event.type == BusEventType.RULE_ACCEPTED:
            rule_id = event.data.get("rule_id", "?")
            if log_level == "DEBUG":
                print(f"    {_DIM}Agent {event.agent_id} accepted rule #{rule_id}{_RESET}")

        elif event.type == BusEventType.RULE_ESTABLISHED:
            text = event.data.get("text", "?")[:80]
            rate = event.data.get("adoption_rate", 0)
            print(f"  {_GREEN}Rule established ({rate:.0%} adoption): \"{text}\"{_RESET}")

        # --- Specialisation ---
        elif event.type == BusEventType.SPECIALISATION_GAINED:
            activity = event.data.get("activity", "?")
            count = event.data.get("count", "?")
            print(f"  {_CYAN}Agent {event.agent_id} specialised in {activity} ({count} repetitions){_RESET}")

        # --- Feedback loops ---
        elif event.type == BusEventType.MAINTENANCE_CONSUMED:
            if log_level == "DEBUG":
                stype = event.data.get("structure_type", "?")
                rtype = event.data.get("resource_type", "?")
                print(f"    {_DIM}Maintenance: {stype} consumed {rtype}{_RESET}")

        elif event.type == BusEventType.CROWDING_EFFECT:
            if log_level == "DEBUG":
                agents_count = event.data.get("agents_on_tile", "?")
                print(f"    {_DIM}Crowding effect: {agents_count} agents on tile{_RESET}")

        elif event.type == BusEventType.TICK_END:
            # Tick end at INFO/DEBUG — minimal separator
            pass

        # Watcher events (Phase 2)
        elif event.type == BusEventType.WATCHER_TICK_REPORT:
            # Condensed one-line summary
            d = event.data
            pop = d.get("population", {})
            structs = d.get("structures", {})
            comp = d.get("composition", {})
            wb = pop.get("avg_wellbeing", 0)
            print(
                f"  {_DIM}Tick {event.tick}: "
                f"{pop.get('total', 0)} agents, "
                f"{structs.get('total', 0)} structures, "
                f"{comp.get('total_recipes', 0)} recipes, "
                f"avg wb {wb:.2f}"
                f"{_RESET}"
            )

        elif event.type == BusEventType.WATCHER_NARRATIVE:
            text = event.data.get("text", "")
            source = event.data.get("source", "")
            if text and source == "chronicler":
                # Chronicler: short, punchy, Attenborough-style
                print(f"\n  {_BOLD}{_CYAN}\u2756 {text}{_RESET}\n")
            elif text:
                border = "=" * 70
                print(f"\n  {_CYAN}{border}{_RESET}")
                print(f"  {_BOLD}{_CYAN}WATCHER — Narrative Report (Tick {event.tick}){_RESET}")
                print(f"  {_CYAN}{border}{_RESET}")
                for line in text.strip().split("\n"):
                    print(f"  {line}")
                print(f"  {_CYAN}{border}{_RESET}\n")

        elif event.type == BusEventType.WATCHER_MILESTONE:
            name = event.data.get("name", "")
            commentary = event.data.get("commentary", "")
            agent_id = event.data.get("agent_id")
            if name in ("Persistent Degradation", "Social Exclusion"):
                # Ethical flag — distinct formatting
                details = event.data.get("details", {})
                agent_str = f" (Agent {agent_id})" if agent_id is not None else ""
                print(f"\n  {_RED}{_BOLD}ETHICAL FLAG: {name}{agent_str}{_RESET}")
                if details:
                    print(f"  {_RED}{details}{_RESET}")
            else:
                # Celebration milestone
                print(f"\n  {_YELLOW}{_BOLD}MILESTONE: {name}{_RESET}")
                if commentary:
                    print(f"  {commentary}")

        sys.stdout.flush()

    return on_event


# ======================================================================
# Legacy decision callable (fallback when AgenticLoop not available)
# ======================================================================

def _make_legacy_decision_callable(llm_client: LLMClient, config: SimulationConfig):
    """Create the async decision callable for the old TickEngine interface.

    Used as a fallback when the AgenticLoop module is not yet available.
    """
    from typing import Any
    from src.types import Action, AgentState, Event, MemoryEntry
    from src.agents.decision import build_prompt, parse_response
    from src.agents.memory import MemoryStore

    async def decide(
        agent: AgentState,
        event: Event,
        world_view: dict[str, Any],
    ) -> Action:
        memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
        memory_summary = memory_store.get_summary(max_entries=20)

        prompt = build_prompt(
            agent=agent,
            events=[event],
            world_view=world_view,
            memory_summary=memory_summary,
        )

        response_text = await llm_client.call_llm(prompt)
        action = parse_response(response_text)

        memory_store.record_event(event)
        memory_store.add(MemoryEntry(
            tick=event.tick,
            summary=f"Decided to {action.type.value}: {action.reasoning[:100]}",
            importance=0.5,
        ))

        return action

    return decide


# ======================================================================
# Main
# ======================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agent Civilisation -- emergent AI social behaviour simulation",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to YAML config file (default: config.yaml)",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=0,
        help="Number of ticks to run (0 = infinite, default: 0)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Force fast mode (ignore ticks_per_real_minute in config)",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start the FastAPI server alongside the simulation (default port 8000)",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8000,
        help="Port for the API server (default: 8000, implies --api)",
    )
    parser.add_argument(
        "--api-host",
        default="0.0.0.0",
        help="Host for the API server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Record per-tick snapshots for replay (saves to snapshots/ directory)",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Compute and print emergence metrics after the run completes",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Export structured run record to this JSON file path",
    )
    parser.add_argument(
        "--preset",
        type=str,
        default="",
        help="Named preset label (for Creator Mode tracking; does not change config)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default="",
        help="Unique run identifier (for Creator Mode tracking)",
    )
    parser.add_argument(
        "--gardener",
        action="store_true",
        help="Enable gardener mode: interactive mid-run intervention between ticks",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Rich terminal dashboard with live panels (replaces plain text output)",
    )
    parser.add_argument(
        "--gardener-interval",
        type=int,
        default=10,
        help="Ticks between gardener prompts (default: 10, only with --gardener)",
    )
    return parser.parse_args()


async def async_main() -> None:
    args = parse_args()
    _run_start_time = time.time()

    # ---- Load config ----
    config_path = os.path.join(_PROJECT_ROOT, args.config)
    if os.path.exists(config_path):
        config = SimulationConfig.from_yaml(config_path)
    else:
        print(f"Config file not found at {config_path}, using defaults.")
        config = SimulationConfig.default()

    if args.fast:
        config.ticks_per_real_minute = 0

    # ---- Logging ----
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("agent_civilisation")

    # ---- Generate world ----
    print(f"{_BOLD}Agent Civilisation{_RESET}")
    print(f"Config: {args.config}")
    print(f"Grid: {config.grid_width}x{config.grid_height} | "
          f"Agents: {config.initial_agent_count} | "
          f"Resources: {', '.join(config.resource_types)}")
    print(f"LLM: {config.model_provider}/{config.model_name} | "
          f"Fast mode: {config.ticks_per_real_minute == 0}")
    print(f"Ticks: {'infinite' if args.ticks == 0 else args.ticks}")
    if _AGENTIC_LOOP_AVAILABLE:
        print(f"Agentic loop: enabled (max {config.max_steps_per_agentic_turn} steps/turn)")
    else:
        print(f"Agentic loop: not available (falling back to legacy single-call mode)")
    print()
    sys.stdout.flush()

    # ---- Try to resume from saved state ----
    state_file = os.path.join(config.save_path, "world_state.json")
    if os.path.exists(state_file):
        try:
            world_state = load_state(config.save_path)
            world = World(world_state.grid_width, world_state.grid_height, world_state.tiles)
            print(f"{_GREEN}Resumed from saved state at tick {world_state.tick} "
                  f"({len(world_state.agents)} agents){_RESET}")
            logger.info(
                "Resumed from tick %d: %d agents",
                world_state.tick, len(world_state.agents),
            )
        except Exception as exc:
            print(f"{_YELLOW}Saved state exists but failed to load: {exc}{_RESET}")
            print(f"{_YELLOW}Generating fresh world...{_RESET}")
            world, world_state = generate_world(config)
            logger.info(
                "World generated: %dx%d grid, %d agents, %d resource types",
                config.grid_width, config.grid_height,
                len(world_state.agents), len(config.resource_types),
            )
    else:
        world, world_state = generate_world(config)
        logger.info(
            "World generated: %dx%d grid, %d agents, %d resource types",
            config.grid_width, config.grid_height,
            len(world_state.agents), len(config.resource_types),
        )

    # ---- Create Event Bus ----
    event_bus = EventBus()

    # ---- Subscribe event handler (dashboard or plain text) ----
    dashboard = None
    if args.dashboard:
        try:
            from src.dashboard import Dashboard, make_dashboard_subscriber
            dashboard = Dashboard(
                config=config,
                total_ticks=args.ticks if args.ticks > 0 else 100,
                preset=args.preset or "default",
            )
            dashboard_handler = make_dashboard_subscriber(dashboard, config)
            event_bus.subscribe(dashboard_handler)
        except ImportError:
            print(f"{_YELLOW}Warning: Rich dashboard not available, falling back to plain text{_RESET}")
            cli_handler = make_cli_subscriber(config, world_state)
            event_bus.subscribe(cli_handler)
    else:
        cli_handler = make_cli_subscriber(config, world_state)
        event_bus.subscribe(cli_handler)

    # ---- Create LLM client ----
    llm_client = LLMClient(config)

    # ---- Create AgenticLoop or fall back to legacy ----
    agentic_loop = None
    decide = None

    if _AGENTIC_LOOP_AVAILABLE and AgenticLoop is not None:
        agentic_loop = AgenticLoop(config, llm_client, event_bus)
        logger.info("AgenticLoop initialized")
    else:
        logger.info("AgenticLoop not available, using legacy decision callable")
        decide = _make_legacy_decision_callable(llm_client, config)

    # ---- Create tick engine ----
    # The TickEngine accepts either the old `decide` callable or the new
    # agentic_loop + event_bus parameters. The other agent is updating
    # TickEngine to accept the new signature.
    engine_kwargs: dict = {
        "world": world,
        "world_state": world_state,
        "config": config,
    }

    # Try new-style constructor first, fall back to legacy
    try:
        engine = TickEngine(
            **engine_kwargs,
            agentic_loop=agentic_loop,
            event_bus=event_bus,
        )
    except TypeError:
        # TickEngine hasn't been updated yet — use legacy constructor
        logger.info("TickEngine does not yet support agentic_loop/event_bus args, using legacy")
        engine = TickEngine(
            **engine_kwargs,
            decide=decide,
        )

    # ---- Create Watcher ----
    chronicle_path = os.path.join(config.log_path, "chronicle.jsonl")
    chronicle = Chronicle(chronicle_path)
    chronicle.load()

    watcher = Watcher(config, event_bus, chronicle, llm_client)
    engine.watcher = watcher

    print(f"Watcher: enabled (narrative every {config.narrative_report_interval} ticks, "
          f"milestones {'on' if config.enable_milestone_reports else 'off'})")
    print(f"Chronicle: {chronicle_path}")
    print()
    sys.stdout.flush()

    # ---- Start API server (optional) ----
    api_server = None
    enable_api = args.api or args.api_port != 8000  # --api-port implies --api

    if enable_api:
        import uvicorn
        from src.api.server import create_app, sim_state as api_sim_state

        # Populate the API's simulation state references.
        api_sim_state.world_state = world_state
        api_sim_state.event_bus = event_bus
        api_sim_state.chronicle = chronicle
        api_sim_state.config = config

        app = create_app()

        uvi_config = uvicorn.Config(
            app,
            host=args.api_host,
            port=args.api_port,
            log_level="warning",
        )
        api_server = uvicorn.Server(uvi_config)

        # Start the uvicorn server as a background asyncio task.
        api_task = asyncio.create_task(api_server.serve())
        print(f"{_CYAN}API server: http://{args.api_host}:{args.api_port}{_RESET}")
        print(f"{_CYAN}WebSocket:  ws://{args.api_host}:{args.api_port}/api/ws/live{_RESET}")
        print()
        sys.stdout.flush()

    # ---- Graceful shutdown ----
    shutdown_requested = False
    original_tick = world_state.tick

    def _handle_signal(signum, frame):
        nonlocal shutdown_requested
        if shutdown_requested:
            print(f"\n{_RED}Force exit.{_RESET}")
            sys.exit(1)
        shutdown_requested = True
        print(f"\n{_YELLOW}Shutting down after current tick... (Ctrl+C again to force){_RESET}")
        engine.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # ---- Run the tick loop ----
    tick_count = 0
    target_ticks = args.ticks if args.ticks > 0 else float("inf")

    # ---- Gardener mode ----
    gardener = None
    if args.gardener:
        try:
            from src.gardener import CLIGardener
            gardener = CLIGardener(interval=args.gardener_interval)
            print(f"{_CYAN}Gardener mode: you'll be prompted every {args.gardener_interval} ticks{_RESET}")
            sys.stdout.flush()
        except ImportError:
            print(f"{_YELLOW}Warning: gardener module not found, continuing without gardener{_RESET}")

    # ---- Start dashboard ----
    if dashboard is not None:
        dashboard.start()

    recording = args.record
    if recording:
        print(f"{_CYAN}Recording mode: per-tick snapshots will be saved to {config.save_path}/snapshots/{_RESET}")
        sys.stdout.flush()
        # Save initial snapshot (tick 0) before any ticks run
        try:
            save_tick_snapshot(world_state, config.save_path)
        except Exception as e:
            logger.warning("Failed to save initial tick snapshot: %s", e)

    try:
        while tick_count < target_ticks and not shutdown_requested:
            # Execute one tick (tick.py emits TICK_START and TICK_END via event bus)
            await engine._execute_tick()

            tick_count += 1

            # Save per-tick snapshot for replay
            if recording:
                try:
                    save_tick_snapshot(world_state, config.save_path)
                except Exception as e:
                    logger.warning("Failed to save tick snapshot: %s", e)

            # Gardener intervention (between ticks)
            if gardener is not None:
                should_continue = gardener.post_tick(world_state, tick_count)
                if not should_continue:
                    break

            # Pacing
            if config.ticks_per_real_minute > 0:
                seconds_per_tick = 60.0 / config.ticks_per_real_minute
                await asyncio.sleep(seconds_per_tick)
            else:
                await asyncio.sleep(0)

    except KeyboardInterrupt:
        pass

    # ---- Stop API server ----
    if api_server is not None:
        api_server.should_exit = True
        # Give uvicorn a moment to shut down gracefully.
        try:
            await asyncio.wait_for(api_task, timeout=3.0)
        except (asyncio.TimeoutError, Exception):
            pass

    # ---- Stop dashboard ----
    if dashboard is not None:
        dashboard.stop()

    # ---- Save state on exit ----
    wall_time = time.time() - _run_start_time
    print(f"\n{_BOLD}Simulation ended.{_RESET} Ran {tick_count} ticks (tick {original_tick} -> {world_state.tick}).")
    try:
        save_state(world_state, config.save_path)
        print(f"State saved to {config.save_path}/")
    except Exception as e:
        print(f"{_RED}Failed to save state: {e}{_RESET}")

    # ---- Compute emergence metrics ----
    if args.metrics or args.output:
        bus_events = event_bus.get_log() if event_bus else None
        emergence = compute_emergence(world_state, bus_events)

        if args.metrics:
            if dashboard is not None:
                dashboard.print_emergence(emergence)
            else:
                print(f"\n{_BOLD}Emergence Metrics{_RESET}")
                print(f"  Composite score:    {emergence.composite_score:.4f}")
                print(f"  Innovations:        {emergence.innovation_count}")
                print(f"  Structures:         {emergence.structure_count} ({emergence.unique_structure_types} types)")
                print(f"  Relationships:      {emergence.relationship_count} ({emergence.bonded_pairs} bonded pairs)")
                print(f"  Rules:              {emergence.rules_proposed} proposed, {emergence.rules_established} established")
                print(f"  Avg wellbeing:      {emergence.avg_wellbeing:.3f}")
                print(f"  Avg Maslow level:   {emergence.avg_maslow_level:.2f}")
                print(f"  Specialisations:    {emergence.total_specialisations} ({emergence.agents_with_specialisation} agents)")
                print(f"  Messages:           {emergence.total_messages}")
                print(f"  Cooperation events: {emergence.cooperation_events}")

        # ---- End-of-run chronicler story ----
        if watcher and watcher.chronicler.commentary_count > 0:
            try:
                story = await watcher.chronicler.tell_story(chronicle, world_state)
                if dashboard is not None:
                    dashboard.print_story(story)
                else:
                    print(f"\n{_CYAN}{'=' * 70}{_RESET}")
                    print(f"{_BOLD}{_CYAN}  The Story of This Civilisation{_RESET}")
                    print(f"{_CYAN}{'=' * 70}{_RESET}\n")
                    for line in story.strip().split("\n"):
                        print(f"  {line}")
                    print(f"\n{_CYAN}{'=' * 70}{_RESET}")
                    print(f"  {_DIM}Chronicler made {watcher.chronicler.commentary_count} observations during the run.{_RESET}")
                    print(f"{_CYAN}{'=' * 70}{_RESET}\n")
            except Exception as e:
                logger.warning("End-of-run story failed: %s", e)

        if args.output:
            # Gather chronicle highlights
            milestones = []
            highlights = []
            for entry in chronicle.entries:
                if entry.get("type") == "milestone":
                    milestones.append(entry.get("data", {}).get("name", ""))
                elif entry.get("type") == "narrative":
                    text = entry.get("data", {}).get("text", "")
                    if text:
                        highlights.append(text[:200])

            # Estimate token usage from LLM client
            total_tokens = getattr(llm_client, "total_tokens", 0)

            record = SimulationRunRecord(
                run_id=args.run_id or f"run_{int(time.time())}",
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                wall_time_seconds=wall_time,
                config_snapshot={
                    "initial_agent_count": config.initial_agent_count,
                    "grid_width": config.grid_width,
                    "grid_height": config.grid_height,
                    "resource_distribution": config.resource_distribution,
                    "model_provider": config.model_provider,
                    "model_name": config.model_name,
                    "enable_innovation": config.enable_innovation,
                    "enable_composition": config.enable_composition,
                    "enable_specialisation": config.enable_specialisation,
                    "enable_collective_rules": config.enable_collective_rules,
                },
                preset=args.preset,
                ticks_completed=tick_count,
                total_tokens=total_tokens,
                emergence=emergence,
                milestones=milestones[:20],
                chronicle_highlights=highlights[:10],
                agent_summary=build_agent_summary(world_state.agents),
                success=True,
            )
            output_path = record.save(args.output)
            print(f"\n{_GREEN}Run record exported to {output_path}{_RESET}")


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
