"""The tick loop — the heart of the simulation.

TickEngine advances the world one tick at a time. Each tick:
  1. Deplete agent needs
  2. Apply capability degradation / recovery
  3. Apply wellbeing decay
  4. Detect events per agent
  5. Queue agents with events (or due for reflection / plan steps) for agentic turns
  6. Execute deterministic behaviour for non-queued agents (plan following or survival)
  7. Run parallel agentic turns for queued agents (async, capped concurrency)
  8. Apply wellbeing bonuses for interactions
  9. Regenerate resources
  10. Check for new agent arrivals
  11. Check for environmental shifts
  12. Save state if interval reached
  13. Increment tick + agent ages
  14. Archive per-tick events/messages, then clear them
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Awaitable, Callable, Optional, Protocol

from src.config import SimulationConfig
from src.types import (
    Action,
    ActionType,
    AgentState,
    BusEvent,
    BusEventType,
    Capabilities,
    Event,
    EventBus,
    EventType,
    Message,
    Position,
    CURIOSITY_MAX,
    CURIOSITY_MIN,
    WELLBEING_MAX,
    WELLBEING_MIN,
    WorldState,
)
from src.engine.world import World
from src.engine.environment import apply_shift, create_new_agent
from src.agents.drives import compute_maslow_level, update_survival_stability, apply_wellbeing_ceiling
from src.engine.persistence import append_bus_events, append_events, append_messages, save_state
from src.engine.structures import (
    build_structure,
    can_build,
    decay_structures,
    describe_structures,
    get_path_cost_multiplier,
    get_shelter_degradation_multiplier,
    get_storage_contents,
    get_need_depletion_reduction,
    get_wellbeing_bonus,
    get_perception_bonus,
    is_in_settlement,
    read_marker,
    retrieve_from_storage,
    store_resource,
)
from src.engine.feedback import (
    apply_maintenance,
    count_agents_on_tile,
    crowding_depletion_rate,
    decay_gathering_pressure,
    effective_regeneration_rate,
    record_gathering_pressure,
)
from src.agents.specialisation import record_activity, get_efficiency_bonus

logger = logging.getLogger("agent_civilisation.tick")


# ======================================================================
# TickEngine
# ======================================================================

class TickEngine:
    """Manages the simulation tick loop.

    Parameters:
        world: The World grid object (spatial queries, resource ops).
        world_state: The mutable WorldState snapshot.
        config: All simulation parameters.
        agentic_loop: Optional AgenticLoop instance for LLM-backed decisions.
                      If None, all agents use deterministic behaviour.
        event_bus: Optional EventBus for streaming events.
                   If None, a no-op bus is used internally.
    """

    def __init__(
        self,
        world: World,
        world_state: Any,  # WorldState — using Any to avoid circular at runtime
        config: SimulationConfig,
        agentic_loop: Any | None = None,  # AgenticLoop (avoid circular import)
        event_bus: EventBus | None = None,
    ) -> None:
        self.world = world
        self.state = world_state
        self.config = config
        self.agentic_loop = agentic_loop
        self.event_bus = event_bus or EventBus()
        self.watcher = None  # Optional[Watcher] — set externally after construction
        self._running = False
        self._rng = random.Random()
        self._bus_log_cursor = 0  # tracks position in bus log for incremental persistence

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Run the tick loop indefinitely until stopped."""
        self._running = True
        while self._running:
            await self._execute_tick()

            # Pacing: if ticks_per_real_minute > 0, sleep to match the target rate.
            # In fast mode (== 0), yield to the event loop so stop() can take effect.
            if self.config.ticks_per_real_minute > 0:
                seconds_per_tick = 60.0 / self.config.ticks_per_real_minute
                await asyncio.sleep(seconds_per_tick)
            else:
                await asyncio.sleep(0)  # yield control

    async def run_for(self, n_ticks: int) -> None:
        """Run exactly *n_ticks* ticks. Useful for testing."""
        for _ in range(n_ticks):
            await self._execute_tick()

    def stop(self) -> None:
        """Signal the run loop to stop after the current tick completes."""
        self._running = False

    # ------------------------------------------------------------------
    # The tick
    # ------------------------------------------------------------------

    async def _execute_tick(self) -> None:
        """Execute one complete tick of the simulation."""
        tick = self.state.tick
        agents = self.state.agents
        config = self.config

        logger.debug("=== Tick %d: %d agents ===", tick, len(agents))

        # Emit TICK_START
        await self.event_bus.emit(BusEvent(
            type=BusEventType.TICK_START,
            tick=tick,
            data={"agent_count": len(agents)},
        ))

        # 1. Deplete all agent needs (adjusted for settlements, rules, and structures)
        # Pre-compute rule bonus: each established rule reduces depletion
        established_rule_count = sum(
            1 for r in self.state.collective_rules if r.established
        )
        rule_reduction = min(
            established_rule_count,
            getattr(config, "max_active_rules", 5),
        ) * getattr(config, "rule_need_depletion_reduction", 0.0)

        for agent in agents.values():
            base_depletion = config.agent_needs_depletion_rate
            effective_depletion = base_depletion

            # Settlement bonus: agents in settlements have slower need drain
            tile = self.world.get_tile(agent.position.x, agent.position.y)
            if tile is not None and is_in_settlement(agent.position, self.world.tiles, config):
                settlement_reduction = getattr(config, "settlement_need_depletion_reduction", 0.0)
                effective_depletion *= (1.0 - settlement_reduction)

            # Custom structure bonus: reduce_need_depletion structures on tile
            if tile is not None:
                struct_reduction = get_need_depletion_reduction(tile)
                effective_depletion *= struct_reduction

            # Rule bonus: established rules reduce depletion for ALL agents
            if rule_reduction > 0:
                effective_depletion *= (1.0 - rule_reduction)

            agent.needs.deplete_all(effective_depletion)

        # 2. Capability degradation or recovery
        for agent in agents.values():
            old_ratio = agent.capabilities.degradation_ratio()
            self._apply_capability_dynamics(agent)
            new_ratio = agent.capabilities.degradation_ratio()
            if abs(new_ratio - old_ratio) > 0.01:
                await self.event_bus.emit(BusEvent(
                    type=BusEventType.DEGRADATION_CHANGED,
                    tick=tick,
                    agent_id=agent.id,
                    data={"old": round(old_ratio, 3), "new": round(new_ratio, 3)},
                ))

        # 3. Wellbeing decay
        for agent in agents.values():
            old_wb = agent.wellbeing
            agent.wellbeing = max(
                WELLBEING_MIN,
                agent.wellbeing - config.agent_wellbeing_decay_rate,
            )
            if abs(agent.wellbeing - old_wb) > 0.001:
                await self.event_bus.emit(BusEvent(
                    type=BusEventType.WELLBEING_CHANGED,
                    tick=tick,
                    agent_id=agent.id,
                    data={"old": round(old_wb, 3), "new": round(agent.wellbeing, 3), "cause": "decay"},
                ))

        # 3a. Settlement and structure wellbeing bonuses
        for agent in agents.values():
            tile = self.world.get_tile(agent.position.x, agent.position.y)
            if tile is None:
                continue

            # Settlement wellbeing bonus
            settlement_wb_bonus = getattr(config, "settlement_wellbeing_bonus", 0.0)
            if settlement_wb_bonus > 0 and is_in_settlement(agent.position, self.world.tiles, config):
                agent.wellbeing = min(WELLBEING_MAX, agent.wellbeing + settlement_wb_bonus)

            # Custom structure wellbeing bonus (boost_wellbeing innovations)
            struct_wb = get_wellbeing_bonus(tile)
            if struct_wb > 0:
                agent.wellbeing = min(WELLBEING_MAX, agent.wellbeing + struct_wb)

            # Custom structure perception bonus (extend_perception innovations)
            perception_boost = get_perception_bonus(tile)
            if perception_boost > 0:
                caps = agent.capabilities
                caps.perception_range = min(
                    caps.base_perception_range + perception_boost,
                    caps.perception_range + perception_boost * 0.1,  # gradual application
                )

        # 3b. Curiosity decay
        for agent in agents.values():
            old_cur = agent.curiosity
            agent.curiosity = max(
                CURIOSITY_MIN,
                agent.curiosity - config.agent_curiosity_decay_rate,
            )

        # 4. Detect events for each agent
        agent_events: dict[int, list[Event]] = {}
        for agent in agents.values():
            events = self._detect_events(agent, tick)
            if events:
                agent_events[agent.id] = events

        # 5 & 6. Split agents into agentic-turn queue and deterministic
        agentic_queue: list[tuple[AgentState, list[Event]]] = []
        deterministic_agents: list[AgentState] = []

        for agent in agents.values():
            events = agent_events.get(agent.id, [])
            reflection_due = (agent.age > 0 and agent.age % config.agent_reflection_interval == 0)
            plan_step_due = len(agent.plan) > 0

            if events:
                # Queue for agentic turn with all triggering events
                agentic_queue.append((agent, events))
                # Store all events for logging
                self.state.events_this_tick.extend(events)

                # Emit NEEDS_CRITICAL bus events for critical needs
                for evt in events:
                    if evt.type == EventType.NEEDS_CRITICAL:
                        await self.event_bus.emit(BusEvent(
                            type=BusEventType.NEEDS_CRITICAL,
                            tick=tick,
                            agent_id=agent.id,
                            data=evt.data,
                        ))

            elif reflection_due:
                reflection_event = Event(
                    type=EventType.REFLECTION,
                    tick=tick,
                    agent_id=agent.id,
                    data={"trigger": "periodic_reflection"},
                )
                agentic_queue.append((agent, [reflection_event]))
                self.state.events_this_tick.append(reflection_event)

            elif plan_step_due:
                # Agent has a plan — trigger an agentic turn to execute the next step
                plan_event = Event(
                    type=EventType.PLAN_STEP_DUE,
                    tick=tick,
                    agent_id=agent.id,
                    data={"next_step": agent.plan[0] if agent.plan else ""},
                )
                agentic_queue.append((agent, [plan_event]))
                self.state.events_this_tick.append(plan_event)

            else:
                deterministic_agents.append(agent)

        # 6. Execute deterministic behaviour for non-queued agents
        for agent in deterministic_agents:
            action = self._deterministic_action(agent)
            agent.current_action = action

            # Execute the deterministic action on the world
            self._process_action(agent, tick)

            # Track activity for specialisation
            new_spec = record_activity(agent, action.type.value, config)
            if new_spec:
                await self.event_bus.emit(BusEvent(
                    type=BusEventType.SPECIALISATION_GAINED,
                    tick=tick,
                    agent_id=agent.id,
                    data={
                        "activity": new_spec,
                        "count": agent.activity_counts.get(new_spec, 0),
                    },
                ))

            # Emit DETERMINISTIC_ACTION
            await self.event_bus.emit(BusEvent(
                type=BusEventType.DETERMINISTIC_ACTION,
                tick=tick,
                agent_id=agent.id,
                data={
                    "action": action.type.value,
                    "reasoning": action.reasoning,
                },
            ))

        # 7. Run agentic turns in parallel (capped concurrency)
        if agentic_queue and self.agentic_loop is not None:
            semaphore = asyncio.Semaphore(config.max_concurrent_llm_calls)

            async def _run_agent_turn(
                agent: AgentState, events: list[Event]
            ) -> None:
                async with semaphore:
                    try:
                        actions = await self.agentic_loop.run_turn(
                            agent, events, self.world, self.state
                        )
                        # The agentic loop already executed all actions on the world.
                        # Record the last action as current_action for display.
                        if actions:
                            agent.current_action = actions[-1]
                    except Exception:
                        logger.exception(
                            "Agentic turn failed for agent %d at tick %d",
                            agent.id, tick,
                        )
                        # Fall back to deterministic behaviour
                        agent.current_action = self._deterministic_action(agent)
                        self._process_action(agent, tick)

            tasks = [_run_agent_turn(a, evts) for a, evts in agentic_queue]
            await asyncio.gather(*tasks)

        elif agentic_queue:
            # No agentic loop provided — fall back to deterministic for all
            for agent, _ in agentic_queue:
                agent.current_action = self._deterministic_action(agent)
                self._process_action(agent, tick)
                # Track activity for specialisation
                new_spec = record_activity(agent, agent.current_action.type.value, config)
                if new_spec:
                    await self.event_bus.emit(BusEvent(
                        type=BusEventType.SPECIALISATION_GAINED,
                        tick=tick,
                        agent_id=agent.id,
                        data={
                            "activity": new_spec,
                            "count": agent.activity_counts.get(new_spec, 0),
                        },
                    ))

        # 8. Wellbeing bonuses for interactions this tick
        for agent in agents.values():
            if agent.interactions_this_tick:
                bonus = 0.0
                for partner_id in agent.interactions_this_tick:
                    if partner_id in agent.relationships and agent.relationships[partner_id].is_bonded:
                        bonus += config.agent_wellbeing_interaction_bonus * config.agent_bond_social_multiplier
                    else:
                        bonus += config.agent_wellbeing_interaction_bonus
                old_wb = agent.wellbeing
                agent.wellbeing = min(WELLBEING_MAX, agent.wellbeing + bonus)
                if agent.wellbeing > old_wb:
                    await self.event_bus.emit(BusEvent(
                        type=BusEventType.WELLBEING_CHANGED,
                        tick=tick,
                        agent_id=agent.id,
                        data={
                            "old": round(old_wb, 3),
                            "new": round(agent.wellbeing, 3),
                            "cause": "interaction",
                        },
                    ))

            # Proximity bonus: agents near others get a small wellbeing bump
            nearby = self.world.get_agents_near(
                agent.position,
                config.agent_communication_range,
                agents,
                exclude_id=agent.id,
            )
            if nearby:
                agent.wellbeing = min(
                    WELLBEING_MAX,
                    agent.wellbeing + config.agent_wellbeing_proximity_bonus,
                )

            # Extra proximity bonus for bonded agents nearby
            for other in nearby:
                if other.id in agent.relationships and agent.relationships[other.id].is_bonded:
                    agent.wellbeing = min(
                        WELLBEING_MAX,
                        agent.wellbeing + config.agent_wellbeing_proximity_bonus,  # double proximity for bonds
                    )

        # 8b. Curiosity bonuses
        for agent in agents.values():
            cur_bonus = 0.0

            # Exploration: visiting new tiles
            pos_tuple = (agent.position.x, agent.position.y)
            if pos_tuple not in agent.visited_tiles:
                agent.visited_tiles.add(pos_tuple)
                cur_bonus += config.agent_curiosity_exploration_bonus

            # Social: meeting new agents
            for other_id in agent.interactions_this_tick:
                if other_id not in agent.met_agents:
                    agent.met_agents.add(other_id)
                    cur_bonus += config.agent_curiosity_social_bonus

            if cur_bonus > 0:
                agent.curiosity = min(CURIOSITY_MAX, agent.curiosity + cur_bonus)

        # 8c. Curiosity bonuses from creative acts (building, innovation, composition)
        # These are tracked as BusEvents, not agent-level Events
        for ev in self.event_bus.get_log(since_tick=tick):
            if ev.agent_id is None:
                continue
            agent = agents.get(ev.agent_id)
            if agent is None:
                continue
            creative_bonus = 0.0
            if ev.type == BusEventType.STRUCTURE_BUILT:
                creative_bonus = config.agent_curiosity_discovery_bonus
            elif ev.type == BusEventType.COMPOSITION_DISCOVERED:
                creative_bonus = config.agent_curiosity_discovery_bonus
            elif ev.type == BusEventType.INNOVATION_SUCCEEDED:
                creative_bonus = config.agent_curiosity_discovery_bonus * 1.5  # extra for true innovation
            elif ev.type in (BusEventType.INNOVATION_FAILED, BusEventType.COMPOSITION_FAILED):
                creative_bonus = config.agent_curiosity_discovery_bonus * 0.5  # partial: trying counts
            if creative_bonus > 0:
                agent.curiosity = min(CURIOSITY_MAX, agent.curiosity + creative_bonus)

        # 8d. Maslow drive updates — survival stability, level computation, wellbeing ceiling
        for agent in agents.values():
            update_survival_stability(agent)
            agent.maslow_level = compute_maslow_level(agent, config)
            apply_wellbeing_ceiling(agent)

        # 9. Regenerate resources (pressure-aware if environmental co-evolution enabled)
        if config.enable_environmental_coevolution:
            self._regenerate_with_pressure(config)
        else:
            self.world.regenerate_all(config)

        # 9b. Decay gathering pressure so resources can recover
        if config.enable_environmental_coevolution:
            decay_gathering_pressure(self.world.tiles)

        # 9c. Structure maintenance — structures consume resources to persist
        maintenance_events = apply_maintenance(self.world.tiles, config)
        for mx, my, structure, rtype in maintenance_events:
            await self.event_bus.emit(BusEvent(
                type=BusEventType.MAINTENANCE_CONSUMED,
                tick=tick,
                data={
                    "structure_type": structure.structure_type.value,
                    "position": {"x": mx, "y": my},
                    "resource_type": rtype,
                },
            ))

        # 9d. Structure decay
        removed_structures = decay_structures(self.world.tiles, config)
        for sx, sy, structure in removed_structures:
            await self.event_bus.emit(BusEvent(
                type=BusEventType.STRUCTURE_DECAYED,
                tick=tick,
                data={
                    "structure_type": structure.structure_type.value,
                    "position": {"x": sx, "y": sy},
                    "builder_id": structure.builder_id,
                },
            ))

        # 10. New agent arrival
        if tick > 0 and tick % config.new_agent_interval == 0:
            new_agent = create_new_agent(self.state, config, self._rng)
            logger.info(
                "Tick %d: New agent %d arrived at (%d, %d)",
                tick, new_agent.id, new_agent.position.x, new_agent.position.y,
            )
            await self.event_bus.emit(BusEvent(
                type=BusEventType.AGENT_ARRIVED,
                tick=tick,
                agent_id=new_agent.id,
                data={
                    "position": {"x": new_agent.position.x, "y": new_agent.position.y},
                },
            ))

        # 11. Environmental shift
        if (
            config.enable_environmental_shifts
            and tick > 0
            and tick % config.shift_interval == 0
        ):
            apply_shift(self.world, config, self._rng)
            # Fire environmental change event for all agents
            for agent in agents.values():
                env_event = Event(
                    type=EventType.ENVIRONMENTAL_CHANGE,
                    tick=tick,
                    agent_id=agent.id,
                    data={"severity": config.shift_severity},
                )
                self.state.events_this_tick.append(env_event)
            logger.info("Tick %d: Environmental shift (%s)", tick, config.shift_severity)

            await self.event_bus.emit(BusEvent(
                type=BusEventType.ENVIRONMENTAL_SHIFT,
                tick=tick,
                data={"severity": config.shift_severity},
            ))

        # 12. Save state
        if tick > 0 and tick % config.save_interval == 0:
            try:
                save_state(self.state, config.save_path)
                logger.debug("Tick %d: State saved", tick)
            except Exception:
                logger.exception("Tick %d: Failed to save state", tick)

        # 13. Increment tick counter and agent ages
        self.state.tick += 1
        for agent in agents.values():
            agent.age += 1

        # 14 & 15. Archive per-tick data to logs, then clear
        if self.state.events_this_tick:
            self.state.event_log.extend(self.state.events_this_tick)
            try:
                append_events(self.state.events_this_tick, config.log_path)
            except Exception:
                logger.exception("Failed to append events to log")

        if self.state.messages_this_tick:
            self.state.message_log.extend(self.state.messages_this_tick)
            try:
                append_messages(self.state.messages_this_tick, config.log_path)
            except Exception:
                logger.exception("Failed to append messages to log")

        self.state.events_this_tick.clear()
        self.state.messages_this_tick.clear()
        for agent in agents.values():
            agent.interactions_this_tick.clear()

        # 15. Watcher observation (after all world updates, before TICK_END)
        if self.watcher is not None:
            try:
                await self.watcher.observe_tick(self.state, tick)
            except Exception:
                logger.exception("Watcher failed at tick %d", tick)

        # Emit TICK_END
        await self.event_bus.emit(BusEvent(
            type=BusEventType.TICK_END,
            tick=tick,
            data={"agent_count": len(agents)},
        ))

        # 16. Persist bus events for this tick to disk
        full_log = self.event_bus._log
        new_events = full_log[self._bus_log_cursor:]
        if new_events:
            try:
                append_bus_events(new_events, config.log_path)
            except Exception:
                logger.exception("Failed to append bus events to log")
        self._bus_log_cursor = len(full_log)

    # ------------------------------------------------------------------
    # Capability dynamics
    # ------------------------------------------------------------------

    def _apply_capability_dynamics(self, agent: AgentState) -> None:
        """Apply degradation or recovery to agent capabilities based on needs.

        See types.py Capabilities docstring for the full flow:
        - ANY need < DEGRADATION_THRESHOLD -> degrade
        - ALL needs >= RECOVERY_THRESHOLD -> recover
        - Between thresholds: no change (hysteresis band)

        Shelter effect: if agent is on a tile with a shelter, degradation
        rate is reduced by the shelter's effect_strength multiplier.
        """
        caps = agent.capabilities
        config = self.config

        if agent.needs.any_critical():
            # Check for shelter effect on current tile
            tile = self.world.get_tile(agent.position.x, agent.position.y)
            shelter_mult = 1.0
            if tile is not None:
                shelter_mult = get_shelter_degradation_multiplier(tile, config)
            effective_rate = config.agent_degradation_rate * shelter_mult

            # DEGRADE: each capability moves toward its minimum
            caps.perception_range = max(
                Capabilities.MIN_PERCEPTION_RANGE,
                caps.perception_range - (caps.perception_range - Capabilities.MIN_PERCEPTION_RANGE) * effective_rate,
            )
            caps.movement_speed = max(
                Capabilities.MIN_MOVEMENT_SPEED,
                caps.movement_speed - (caps.movement_speed - Capabilities.MIN_MOVEMENT_SPEED) * effective_rate,
            )
            caps.memory_capacity = max(
                Capabilities.MIN_MEMORY_CAPACITY,
                int(caps.memory_capacity - (caps.memory_capacity - Capabilities.MIN_MEMORY_CAPACITY) * effective_rate),
            )

        elif agent.wellbeing < 0.25 or agent.curiosity < 0.2:
            # Gentle degradation from social/creative deprivation (half survival rate)
            gentle_rate = config.agent_degradation_rate * 0.5
            caps.perception_range = max(
                Capabilities.MIN_PERCEPTION_RANGE,
                caps.perception_range - (caps.perception_range - Capabilities.MIN_PERCEPTION_RANGE) * gentle_rate,
            )
            caps.movement_speed = max(
                Capabilities.MIN_MOVEMENT_SPEED,
                caps.movement_speed - (caps.movement_speed - Capabilities.MIN_MOVEMENT_SPEED) * gentle_rate,
            )

        elif agent.needs.all_healthy():
            # RECOVER: each capability moves toward its base
            caps.perception_range = min(
                caps.base_perception_range,
                caps.perception_range + (caps.base_perception_range - caps.perception_range) * config.agent_recovery_rate,
            )
            caps.movement_speed = min(
                caps.base_movement_speed,
                caps.movement_speed + (caps.base_movement_speed - caps.movement_speed) * config.agent_recovery_rate,
            )
            caps.memory_capacity = min(
                caps.base_memory_capacity,
                int(caps.memory_capacity + (caps.base_memory_capacity - caps.memory_capacity) * config.agent_recovery_rate),
            )

        # Between thresholds: no change (hysteresis band prevents jitter)

        # Curiosity effect on perception
        curiosity_perception_mod = 0.0
        if agent.curiosity > 0.7:
            curiosity_perception_mod = (agent.curiosity - 0.7) * 3.0  # up to +0.9 tiles
        elif agent.curiosity < 0.3:
            curiosity_perception_mod = -(0.3 - agent.curiosity) * 2.0  # down to -0.6 tiles

        if curiosity_perception_mod != 0:
            caps.perception_range = max(
                Capabilities.MIN_PERCEPTION_RANGE,
                min(
                    caps.base_perception_range + 1.0,  # hard cap: base + 1
                    caps.perception_range + curiosity_perception_mod * 0.1,  # gradual
                ),
            )

    # ------------------------------------------------------------------
    # Resource regeneration (pressure-aware)
    # ------------------------------------------------------------------

    def _regenerate_with_pressure(self, config: SimulationConfig) -> None:
        """Regenerate resources using pressure-adjusted rates WITH structure bonuses.

        Negative feedback: heavy gathering reduces regen.
        Positive feedback: structures on tile boost regen (cultivated land).
        """
        for x in range(self.world.width):
            for y in range(self.world.height):
                tile = self.world.tiles[x][y]
                for resource in tile.resources.values():
                    if resource.amount < resource.max_amount:
                        eff_rate = effective_regeneration_rate(resource, tile, config)
                        resource.amount = min(
                            resource.max_amount,
                            resource.amount + eff_rate,
                        )

    # ------------------------------------------------------------------
    # Event detection
    # ------------------------------------------------------------------

    def _detect_events(self, agent: AgentState, tick: int) -> list[Event]:
        """Detect meaningful events for *agent* this tick."""
        events: list[Event] = []
        config = self.config

        # --- Perception: agents entering / leaving range ---
        visible_now: set[int] = set()
        nearby = self.world.get_agents_near(
            agent.position,
            agent.capabilities.perception_range,
            self.state.agents,
            exclude_id=agent.id,
        )
        for other in nearby:
            visible_now.add(other.id)

        # New agents in perception
        entered = visible_now - agent.agents_in_perception
        for aid in entered:
            events.append(Event(
                type=EventType.AGENT_ENTERED_PERCEPTION,
                tick=tick,
                agent_id=agent.id,
                data={"other_agent_id": aid},
            ))

        # Agents that left perception
        left = agent.agents_in_perception - visible_now
        for aid in left:
            events.append(Event(
                type=EventType.AGENT_LEFT_PERCEPTION,
                tick=tick,
                agent_id=agent.id,
                data={"other_agent_id": aid},
            ))

        # Update perception set
        agent.agents_in_perception = visible_now

        # --- Resource discovery / depletion ---
        current_resources = self.world.get_resources_at(agent.position)
        pos_key = (agent.position.x, agent.position.y)

        # Check visible tiles for resource changes
        pr = int(agent.capabilities.perception_range)
        for dx in range(-pr, pr + 1):
            for dy in range(-pr, pr + 1):
                nx, ny = agent.position.x + dx, agent.position.y + dy
                if not self.world.in_bounds(nx, ny):
                    continue
                tile_key = (nx, ny)
                tile_resources = self.world.get_resources_at(Position(nx, ny))

                # Discovery: new resource found that agent didn't know about
                for rtype in tile_resources:
                    if tile_key not in agent.known_resources or agent.known_resources.get(tile_key) != rtype:
                        # Only fire once per resource type per tile
                        if tile_resources[rtype].amount > 0:
                            events.append(Event(
                                type=EventType.RESOURCE_DISCOVERED,
                                tick=tick,
                                agent_id=agent.id,
                                data={"position": [nx, ny], "resource_type": rtype},
                            ))
                            agent.known_resources[tile_key] = rtype

                # Depletion: known resource is now gone
                if tile_key in agent.known_resources:
                    known_type = agent.known_resources[tile_key]
                    if known_type not in tile_resources or tile_resources.get(known_type, None) is None:
                        events.append(Event(
                            type=EventType.RESOURCE_DEPLETED,
                            tick=tick,
                            agent_id=agent.id,
                            data={"position": [nx, ny], "resource_type": known_type},
                        ))
                        del agent.known_resources[tile_key]

        # --- Needs critical ---
        if agent.needs.any_critical():
            lowest_type, lowest_val = agent.needs.lowest()
            events.append(Event(
                type=EventType.NEEDS_CRITICAL,
                tick=tick,
                agent_id=agent.id,
                data={"need": lowest_type, "level": lowest_val},
            ))

        return events

    # ------------------------------------------------------------------
    # Deterministic behaviour (no LLM needed)
    # ------------------------------------------------------------------

    def _deterministic_action(self, agent: AgentState) -> Action:
        """Choose a deterministic action for an agent without LLM.

        Priority:
          0. If agent has a plan, execute the first step deterministically
          1. If at a tile with a needed resource, gather it
          2. If a needed resource is known, move toward it
          3. Explore (random movement)
        """
        # --- Plan following: if agent has plan steps, execute the first one ---
        if agent.plan:
            action = self._execute_plan_step(agent)
            if action is not None:
                return action

        # --- Standard survival behaviour ---

        # What resource does the agent need most?
        lowest_type, lowest_val = agent.needs.lowest()

        # 0b. Consume from inventory if holding a needed resource and need is low
        if lowest_val < 0.5 and lowest_type in agent.inventory:
            return Action(
                type=ActionType.CONSUME,
                resource_type=lowest_type,
                reasoning="consuming needed resource from inventory",
            )

        # 1. Gather if standing on a needed resource
        current_res = self.world.get_resources_at(agent.position)
        if lowest_type in current_res and current_res[lowest_type].amount > 0:
            return Action(
                type=ActionType.GATHER,
                resource_type=lowest_type,
                reasoning="gathering needed resource",
            )

        # Also gather any resource that the agent has below 0.7 satisfaction
        for rtype, res in current_res.items():
            if res.amount > 0 and agent.needs.levels.get(rtype, 1.0) < 0.7:
                return Action(
                    type=ActionType.GATHER,
                    resource_type=rtype,
                    reasoning="gathering available resource",
                )

        # 2. Move toward known resource of the most-needed type
        best_pos: Position | None = None
        best_dist = float("inf")
        for (rx, ry), rtype in agent.known_resources.items():
            if rtype == lowest_type:
                pos = Position(rx, ry)
                d = agent.position.distance_to(pos)
                if d < best_dist:
                    best_dist = d
                    best_pos = pos

        if best_pos is not None:
            dx = _sign(best_pos.x - agent.position.x)
            dy = _sign(best_pos.y - agent.position.y)
            return Action(
                type=ActionType.MOVE,
                direction=(dx, dy),
                reasoning=f"moving toward known {lowest_type}",
            )

        # 3. Explore: random movement
        dx = self._rng.choice([-1, 0, 1])
        dy = self._rng.choice([-1, 0, 1])
        if dx == 0 and dy == 0:
            dx = self._rng.choice([-1, 1])
        return Action(
            type=ActionType.MOVE,
            direction=(dx, dy),
            reasoning="exploring",
        )

    def _execute_plan_step(self, agent: AgentState) -> Action | None:
        """Try to execute the first step of the agent's plan deterministically.

        Pops the step from the plan if successfully interpreted.
        Returns None if the step can't be interpreted as a deterministic action.
        """
        if not agent.plan:
            return None

        step_text = agent.plan[0].lower().strip()

        # Try to interpret the plan step as a basic action
        # --- gather ---
        if "gather" in step_text:
            for rtype in self.config.resource_types:
                if rtype in step_text:
                    current_res = self.world.get_resources_at(agent.position)
                    if rtype in current_res and current_res[rtype].amount > 0:
                        agent.plan.pop(0)
                        agent.current_routine = "following_plan"
                        return Action(
                            type=ActionType.GATHER,
                            resource_type=rtype,
                            reasoning=f"plan step: {step_text}",
                        )
                    # Resource not here — move toward it if known
                    for (rx, ry), kr_type in agent.known_resources.items():
                        if kr_type == rtype:
                            dx = _sign(rx - agent.position.x)
                            dy = _sign(ry - agent.position.y)
                            agent.current_routine = "following_plan"
                            return Action(
                                type=ActionType.MOVE,
                                direction=(dx, dy),
                                reasoning=f"plan step: moving toward {rtype} to {step_text}",
                            )

        # --- move toward / explore ---
        if "move" in step_text or "explore" in step_text or "go" in step_text:
            # Try directional movement
            for dir_name, direction in _DIRECTION_MAP.items():
                if dir_name in step_text:
                    agent.plan.pop(0)
                    agent.current_routine = "following_plan"
                    return Action(
                        type=ActionType.MOVE,
                        direction=direction,
                        reasoning=f"plan step: {step_text}",
                    )

            # Generic "explore" — random direction, pop step
            agent.plan.pop(0)
            agent.current_routine = "following_plan"
            dx = self._rng.choice([-1, 0, 1])
            dy = self._rng.choice([-1, 0, 1])
            if dx == 0 and dy == 0:
                dx = self._rng.choice([-1, 1])
            return Action(
                type=ActionType.MOVE,
                direction=(dx, dy),
                reasoning=f"plan step: {step_text}",
            )

        # --- wait ---
        if "wait" in step_text or "rest" in step_text:
            agent.plan.pop(0)
            agent.current_routine = "following_plan"
            return Action(
                type=ActionType.WAIT,
                reasoning=f"plan step: {step_text}",
            )

        # Can't interpret this step deterministically — pop it so we don't loop
        # The agent will get an agentic turn on the next tick if more steps remain
        agent.plan.pop(0)
        return None

    # ------------------------------------------------------------------
    # Action processing (for deterministic agents and fallback)
    # ------------------------------------------------------------------

    def _process_action(self, agent: AgentState, tick: int) -> None:
        """Execute the agent's current_action on the world."""
        action = agent.current_action
        if action is None:
            return

        if action.type == ActionType.MOVE:
            self._process_move(agent, action, tick)

        elif action.type == ActionType.GATHER:
            self._process_gather(agent, action, tick)

        elif action.type == ActionType.COMMUNICATE:
            self._process_communicate(agent, action, tick)

        elif action.type == ActionType.BUILD:
            self._process_build(agent, action, tick)

        elif action.type == ActionType.CONSUME:
            self._process_consume(agent, action, tick)

        elif action.type == ActionType.STORE:
            self._process_store(agent, action, tick)

        elif action.type == ActionType.READ_MARKER:
            self._process_read_marker(agent, action, tick)

        elif action.type in (
            ActionType.COMPOSE,
            ActionType.PROPOSE_INNOVATION,
            ActionType.PROPOSE_RULE,
            ActionType.ACCEPT_RULE,
            ActionType.IGNORE_RULE,
        ):
            # These actions require LLM evaluation or world_state access
            # that the agentic loop handles. Deterministic agents won't
            # attempt these — they fall through to no-op here.
            pass

        elif action.type == ActionType.WAIT:
            pass  # Agent does nothing

    def _process_move(self, agent: AgentState, action: Action, tick: int) -> None:
        """Move the agent in the specified direction, respecting terrain cost.

        Path structures reduce the effective movement cost on the target tile.
        """
        if action.direction is None:
            return

        dx, dy = action.direction
        new_x = agent.position.x + dx
        new_y = agent.position.y + dy

        # Bounds check
        if not self.world.in_bounds(new_x, new_y):
            return

        # Terrain movement cost check (with path structure bonus)
        target_tile = self.world.get_tile(new_x, new_y)
        if target_tile is None:
            return

        terrain_name = target_tile.terrain.value
        base_cost = self.config.movement_cost.get(terrain_name, 1)
        path_mult = get_path_cost_multiplier(target_tile, self.config)
        cost = base_cost * path_mult

        # Movement specialisation bonus: movement specialists move faster
        move_bonus = get_efficiency_bonus(agent, "move", self.config)
        effective_speed = agent.capabilities.movement_speed * move_bonus

        # Agent can move if effective_speed / cost >= 1
        if effective_speed / cost >= 1.0:
            agent.position = Position(new_x, new_y)
        else:
            # Probabilistic movement: agent has a chance proportional to speed/cost
            if self._rng.random() < (effective_speed / cost):
                agent.position = Position(new_x, new_y)

    def _process_gather(self, agent: AgentState, action: Action, tick: int) -> None:
        """Gather a resource from the current tile into agent inventory.

        Resources go to inventory (not directly to needs). Agents must use
        the CONSUME action to convert inventory resources into need satisfaction.
        Also checks storage structures if tile has no natural resources.

        Crowding: if multiple agents are on the same tile, depletion is faster.
        Gathering pressure: tracks how heavily a resource is being exploited.
        """
        if action.resource_type is None:
            return

        # Check inventory capacity
        if len(agent.inventory) >= self.config.agent_carry_capacity:
            logger.debug(
                "Agent %d inventory full (%d/%d), cannot gather",
                agent.id, len(agent.inventory), self.config.agent_carry_capacity,
            )
            return

        # Crowding: count agents on same tile for depletion multiplier
        agents_here = count_agents_on_tile(agent.position, self.state.agents)
        base_rate = self.config.resource_depletion_rate
        # Specialisation bonus: gathering specialists extract more
        spec_bonus = get_efficiency_bonus(agent, "gather", self.config)
        effective_rate = crowding_depletion_rate(base_rate * spec_bonus, agents_here, self.config)

        # Try natural tile resources first
        depleted = self.world.deplete_resource(
            agent.position,
            action.resource_type,
            effective_rate,
        )

        if depleted > 0:
            agent.inventory.append(action.resource_type)

            # Record gathering pressure for environmental co-evolution
            tile = self.world.get_tile(agent.position.x, agent.position.y)
            if tile is not None:
                record_gathering_pressure(tile, action.resource_type, depleted)

            logger.debug(
                "Agent %d gathered %s at (%d, %d) -> inventory (%d/%d)%s",
                agent.id, action.resource_type,
                agent.position.x, agent.position.y,
                len(agent.inventory), self.config.agent_carry_capacity,
                f" [crowding x{agents_here}]" if agents_here > 1 else "",
            )
            return

        # Try storage structures on the tile
        tile = self.world.get_tile(agent.position.x, agent.position.y)
        if tile is not None and retrieve_from_storage(tile, action.resource_type):
            agent.inventory.append(action.resource_type)
            logger.debug(
                "Agent %d took %s from storage at (%d, %d) -> inventory",
                agent.id, action.resource_type,
                agent.position.x, agent.position.y,
            )

    def _process_communicate(self, agent: AgentState, action: Action, tick: int) -> None:
        """Send a message from agent to target (or broadcast)."""
        if action.message is None:
            return

        target_id = action.target_agent_id
        config = self.config
        # Communication specialisation bonus: specialists have extended range
        comm_bonus = get_efficiency_bonus(agent, "communicate", config)
        effective_range = config.agent_communication_range * comm_bonus

        if target_id is not None and target_id == -1:
            # Broadcast to all agents in communication range
            nearby = self.world.get_agents_near(
                agent.position,
                effective_range,
                self.state.agents,
                exclude_id=agent.id,
            )
            for other in nearby:
                self._deliver_message(agent, other, action.message, tick)
        elif target_id is not None and target_id in self.state.agents:
            # Direct message to specific agent
            target = self.state.agents[target_id]
            if agent.position.distance_to(target.position) <= effective_range:
                self._deliver_message(agent, target, action.message, tick)
        else:
            # No valid target — broadcast
            nearby = self.world.get_agents_near(
                agent.position,
                effective_range,
                self.state.agents,
                exclude_id=agent.id,
            )
            for other in nearby:
                self._deliver_message(agent, other, action.message, tick)

    def _process_build(self, agent: AgentState, action: Action, tick: int) -> None:
        """Build a structure on the agent's current tile."""
        stype = action.structure_type
        if stype is None:
            return

        tile = self.world.get_tile(agent.position.x, agent.position.y)
        if tile is None:
            return

        structure = build_structure(
            agent, stype, tile, self.config, tick,
            message=action.marker_message,
        )
        # build_structure returns None if requirements not met (no bus event)

    def _process_consume(self, agent: AgentState, action: Action, tick: int) -> None:
        """Consume a resource from inventory to satisfy the corresponding need."""
        rtype = action.resource_type
        if rtype is None:
            return

        if rtype in agent.inventory:
            agent.inventory.remove(rtype)
            agent.needs.satisfy(rtype, self.config.agent_gather_restore)
            logger.debug(
                "Agent %d consumed %s from inventory, %s need now %.2f",
                agent.id, rtype, rtype, agent.needs.levels.get(rtype, 0),
            )

    def _process_store(self, agent: AgentState, action: Action, tick: int) -> None:
        """Store a held resource into a storage structure on the current tile."""
        rtype = action.resource_type
        if rtype is None:
            return

        tile = self.world.get_tile(agent.position.x, agent.position.y)
        if tile is None:
            return

        store_resource(agent, tile, rtype)

    def _process_read_marker(self, agent: AgentState, action: Action, tick: int) -> None:
        """Read marker messages on the current tile."""
        tile = self.world.get_tile(agent.position.x, agent.position.y)
        if tile is None:
            return

        markers = read_marker(tile)
        # Store marker contents as memories
        from src.agents.memory import MemoryStore
        from src.types import MemoryEntry
        memory_store = MemoryStore(agent.memories, agent.capabilities.memory_capacity)
        for builder_id, message in markers:
            memory_store.add(MemoryEntry(
                tick=tick,
                summary=f"Read marker from Entity {builder_id}: {message}",
                importance=0.7,
            ))

    def _deliver_message(
        self,
        sender: AgentState,
        receiver: AgentState,
        content: str,
        tick: int,
    ) -> None:
        """Deliver a message and record the interaction."""
        msg = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            content=content,
            tick=tick,
        )
        self.state.messages_this_tick.append(msg)

        # Track interactions for wellbeing bonuses
        if receiver.id not in sender.interactions_this_tick:
            sender.interactions_this_tick.append(receiver.id)
        if sender.id not in receiver.interactions_this_tick:
            receiver.interactions_this_tick.append(sender.id)

        # Emit MESSAGE_SENT to event bus (powers watcher communication stats)
        self.event_bus.emit_sync(BusEvent(
            type=BusEventType.MESSAGE_SENT,
            tick=tick,
            agent_id=sender.id,
            data={
                "sender_id": sender.id,
                "receiver_id": receiver.id,
                "content": content[:500],
            },
        ))

        # Fire RECEIVED_MESSAGE event on receiver — may queue them for
        # LLM call next tick (we don't re-queue mid-tick to keep things clean,
        # but the event is recorded so the receiver can react next tick).
        recv_event = Event(
            type=EventType.RECEIVED_MESSAGE,
            tick=tick,
            agent_id=receiver.id,
            data={
                "sender_id": sender.id,
                "content": content,
            },
        )
        self.state.events_this_tick.append(recv_event)

        logger.debug(
            "Agent %d -> Agent %d: '%s'",
            sender.id, receiver.id, content[:60],
        )

    # ------------------------------------------------------------------
    # World view builder (for LLM prompts / inspection)
    # ------------------------------------------------------------------

    def _build_world_view(self, agent: AgentState) -> dict[str, Any]:
        """Build the perception dict passed to the LLM decide callable.

        Contains everything the agent can perceive: nearby tiles,
        resources, agents, and its own state.
        """
        pr = int(agent.capabilities.perception_range)
        visible_tiles: list[dict[str, Any]] = []
        visible_resources: list[dict[str, Any]] = []
        visible_agents: list[dict[str, Any]] = []

        for dx in range(-pr, pr + 1):
            for dy in range(-pr, pr + 1):
                nx, ny = agent.position.x + dx, agent.position.y + dy
                tile = self.world.get_tile(nx, ny)
                if tile is None:
                    continue
                tile_info: dict[str, Any] = {
                    "x": nx,
                    "y": ny,
                    "terrain": tile.terrain.value,
                }
                visible_tiles.append(tile_info)

                for rtype, res in tile.resources.items():
                    if res.amount > 0:
                        visible_resources.append({
                            "x": nx,
                            "y": ny,
                            "type": rtype,
                            "amount": round(res.amount, 2),
                        })

        # Visible agents
        nearby = self.world.get_agents_near(
            agent.position,
            agent.capabilities.perception_range,
            self.state.agents,
            exclude_id=agent.id,
        )
        for other in nearby:
            visible_agents.append({
                "id": other.id,
                "x": other.position.x,
                "y": other.position.y,
                "distance": agent.position.distance_to(other.position),
            })

        # Structures visible on tiles
        visible_structures: list[dict[str, Any]] = []
        for dx in range(-pr, pr + 1):
            for dy in range(-pr, pr + 1):
                nx, ny = agent.position.x + dx, agent.position.y + dy
                tile = self.world.get_tile(nx, ny)
                if tile is not None:
                    for s in tile.structures:
                        if s.health > 0:
                            struct_info: dict[str, Any] = {
                                "x": nx,
                                "y": ny,
                                "type": s.structure_type.value,
                                "health": round(s.health, 2),
                                "builder_id": s.builder_id,
                            }
                            if s.message:
                                struct_info["message"] = s.message
                            if s.stored_resources:
                                struct_info["stored"] = dict(s.stored_resources)
                            visible_structures.append(struct_info)

        return {
            "agent_id": agent.id,
            "position": {"x": agent.position.x, "y": agent.position.y},
            "needs": dict(agent.needs.levels),
            "wellbeing": round(agent.wellbeing, 3),
            "capabilities": {
                "perception_range": round(agent.capabilities.perception_range, 2),
                "movement_speed": round(agent.capabilities.movement_speed, 2),
                "memory_capacity": agent.capabilities.memory_capacity,
            },
            "degradation": round(agent.capabilities.degradation_ratio(), 3),
            "inventory": list(agent.inventory),
            "carry_capacity": self.config.agent_carry_capacity,
            "visible_tiles": visible_tiles,
            "visible_resources": visible_resources,
            "visible_agents": visible_agents,
            "visible_structures": visible_structures,
            "memories": [
                {"tick": m.tick, "summary": m.summary}
                for m in agent.memories[-20:]  # Last 20 memories for context window
            ],
            "goals": agent.goals,
            "plan": agent.plan,
            "current_routine": agent.current_routine,
            "age": agent.age,
        }


# ======================================================================
# Direction map (for deterministic plan step parsing)
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
}


# ======================================================================
# Utility
# ======================================================================

def _sign(n: int) -> int:
    """Return -1, 0, or 1 depending on sign of n."""
    if n > 0:
        return 1
    elif n < 0:
        return -1
    return 0
