"""Milestone detection for the Watcher.

Heuristic checks run every tick. When a milestone fires for the first
time, optional LLM commentary is generated. Ethical flags are recorded
without LLM commentary.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from src.config import SimulationConfig
from src.types import (
    BusEventType,
    EventBus,
    Position,
    StructureType,
    WorldState,
)

logger = logging.getLogger("agent_civilisation.watcher.milestone")


class MilestoneDetector:
    """Tracks which milestones have fired and checks for new ones each tick."""

    def __init__(self) -> None:
        self._fired: set[str] = set()
        # Tracking state for multi-tick milestones
        self._degradation_streaks: dict[int, int] = {}  # agent_id -> consecutive ticks with high degradation
        self._agent_positions: dict[int, list[Position]] = {}  # agent_id -> last N positions

    async def check_milestones(
        self,
        world_state: WorldState,
        event_bus: EventBus,
        tick: int,
        config: SimulationConfig,
        llm_client,
    ) -> list[dict]:
        """Check all milestone conditions and return newly fired milestones.

        Returns:
            List of {"name": str, "tick": int, "commentary": str} for
            each milestone that fired this tick.
        """
        results: list[dict] = []

        # ---- Social milestones ----
        await self._check(
            "First Contact",
            self._check_first_contact(event_bus),
            tick, llm_client, results,
        )
        await self._check(
            "First Cluster",
            self._check_first_cluster(world_state),
            tick, llm_client, results,
        )
        await self._check(
            "First Collective Rule",
            self._check_event_exists(event_bus, BusEventType.RULE_PROPOSED),
            tick, llm_client, results,
        )
        await self._check(
            "First Established Rule",
            self._check_event_exists(event_bus, BusEventType.RULE_ESTABLISHED),
            tick, llm_client, results,
        )
        await self._check(
            "First Specialisation",
            self._check_event_exists(event_bus, BusEventType.SPECIALISATION_GAINED),
            tick, llm_client, results,
        )
        await self._check(
            "Division of Labour",
            self._check_division_of_labour(world_state),
            tick, llm_client, results,
        )

        # ---- Civilisational milestones ----
        await self._check(
            "First Structure",
            self._check_event_exists(event_bus, BusEventType.STRUCTURE_BUILT),
            tick, llm_client, results,
        )
        await self._check(
            "First Settlement",
            self._check_first_settlement(world_state),
            tick, llm_client, results,
        )
        await self._check(
            "First Storage Surplus",
            self._check_first_storage_surplus(world_state),
            tick, llm_client, results,
        )
        await self._check(
            "First Path Network",
            self._check_first_path_network(world_state),
            tick, llm_client, results,
        )
        await self._check(
            "First Composition",
            self._check_event_exists(event_bus, BusEventType.COMPOSITION_DISCOVERED),
            tick, llm_client, results,
        )
        await self._check(
            "First Innovation",
            self._check_event_exists(event_bus, BusEventType.INNOVATION_SUCCEEDED),
            tick, llm_client, results,
        )
        await self._check(
            "Innovation Wave",
            self._check_innovation_wave(event_bus, tick),
            tick, llm_client, results,
        )
        await self._check(
            "Settlement Network",
            self._check_settlement_network(world_state),
            tick, llm_client, results,
        )

        # ---- Feedback milestones ----
        await self._check(
            "First Crowding Crisis",
            self._check_first_crowding_crisis(event_bus),
            tick, llm_client, results,
        )
        await self._check(
            "First Maintenance Failure",
            self._check_first_maintenance_failure(event_bus, world_state),
            tick, llm_client, results,
        )
        await self._check(
            "First Environmental Degradation",
            self._check_first_env_degradation(world_state),
            tick, llm_client, results,
        )
        await self._check(
            "Resource Migration",
            self._check_resource_migration(world_state, event_bus, tick),
            tick, llm_client, results,
        )

        # ---- Ethical flags (no LLM commentary) ----
        ethical_flags = self._check_ethical_flags(world_state, event_bus, tick)
        for flag in ethical_flags:
            results.append(flag)

        return results

    # ------------------------------------------------------------------
    # Core check dispatcher
    # ------------------------------------------------------------------

    async def _check(
        self,
        name: str,
        condition: bool,
        tick: int,
        llm_client,
        results: list[dict],
    ) -> None:
        """If condition is True and milestone hasn't fired yet, fire it."""
        if name in self._fired:
            return
        if not condition:
            return

        self._fired.add(name)
        commentary = await self._generate_commentary(name, tick, llm_client)
        results.append({
            "name": name,
            "tick": tick,
            "commentary": commentary,
        })
        logger.info("Milestone fired: %s at tick %d", name, tick)

    async def _generate_commentary(
        self, name: str, tick: int, llm_client
    ) -> str:
        """Generate a 1-2 sentence LLM commentary for a milestone."""
        prompt = (
            f"In a simulation of AI agents building a civilisation from scratch, "
            f"the milestone '{name}' just occurred at tick {tick}. "
            f"Write one sentence about what this means for the civilisation's development."
        )
        try:
            return await llm_client.call_llm(prompt)
        except Exception:
            logger.warning("Failed to generate commentary for milestone '%s'", name)
            return f"Milestone '{name}' reached at tick {tick}."

    # ------------------------------------------------------------------
    # Social milestone checks
    # ------------------------------------------------------------------

    def _check_first_contact(self, event_bus: EventBus) -> bool:
        """MESSAGE_SENT event count reaches 1 across all time."""
        return len(event_bus.get_log_by_type(BusEventType.MESSAGE_SENT)) >= 1

    def _check_first_cluster(self, world_state: WorldState) -> bool:
        """3 or more agents within Chebyshev distance 2 of each other."""
        agents = list(world_state.agents.values())
        n = len(agents)
        for i in range(n):
            nearby = [agents[i]]
            for j in range(n):
                if i == j:
                    continue
                if agents[i].position.distance_to(agents[j].position) <= 2:
                    nearby.append(agents[j])
            if len(nearby) >= 3:
                # Verify all pairs within distance 2
                all_close = True
                for a in range(len(nearby)):
                    for b in range(a + 1, len(nearby)):
                        if nearby[a].position.distance_to(nearby[b].position) > 2:
                            all_close = False
                            break
                    if not all_close:
                        break
                if all_close:
                    return True
        return False

    def _check_division_of_labour(self, world_state: WorldState) -> bool:
        """3 or more agents with different specialisations within distance 3."""
        specialised = [
            a for a in world_state.agents.values() if a.specialisations
        ]
        if len(specialised) < 3:
            return False

        for i, agent_a in enumerate(specialised):
            nearby_specs: dict[str, int] = {}
            # Count agent_a's specs
            for s in agent_a.specialisations:
                nearby_specs[s] = nearby_specs.get(s, 0) + 1

            nearby_count = 1  # agent_a itself
            for j, agent_b in enumerate(specialised):
                if i == j:
                    continue
                if agent_a.position.distance_to(agent_b.position) <= 3:
                    nearby_count += 1
                    for s in agent_b.specialisations:
                        nearby_specs[s] = nearby_specs.get(s, 0) + 1

            if nearby_count >= 3 and len(nearby_specs) >= 3:
                return True

        return False

    # ------------------------------------------------------------------
    # Civilisational milestone checks
    # ------------------------------------------------------------------

    def _check_event_exists(
        self, event_bus: EventBus, event_type: BusEventType
    ) -> bool:
        """Check if at least one event of the given type exists across all time."""
        return len(event_bus.get_log_by_type(event_type)) >= 1

    def _check_first_settlement(self, world_state: WorldState) -> bool:
        """3 or more structures within Chebyshev distance 2."""
        struct_positions: list[Position] = []
        for x, col in enumerate(world_state.tiles):
            for y, tile in enumerate(col):
                for s in tile.structures:
                    if s.health > 0:
                        struct_positions.append(Position(x, y))

        if len(struct_positions) < 3:
            return False

        for i, pos_a in enumerate(struct_positions):
            nearby = 1
            for j, pos_b in enumerate(struct_positions):
                if i == j:
                    continue
                if pos_a.distance_to(pos_b) <= 2:
                    nearby += 1
            if nearby >= 3:
                return True
        return False

    def _check_first_storage_surplus(self, world_state: WorldState) -> bool:
        """Any storage structure with sum of stored resources > 5."""
        for col in world_state.tiles:
            for tile in col:
                for s in tile.structures:
                    if (
                        s.structure_type == StructureType.STORAGE
                        and s.health > 0
                        and sum(s.stored_resources.values()) > 5
                    ):
                        return True
        return False

    def _check_first_path_network(self, world_state: WorldState) -> bool:
        """3 or more path structures forming a connected chain (adjacent tiles)."""
        path_positions: set[tuple[int, int]] = set()
        for x, col in enumerate(world_state.tiles):
            for y, tile in enumerate(col):
                for s in tile.structures:
                    if s.structure_type == StructureType.PATH and s.health > 0:
                        path_positions.add((x, y))

        if len(path_positions) < 3:
            return False

        # BFS to find connected components
        visited: set[tuple[int, int]] = set()
        for start in path_positions:
            if start in visited:
                continue
            component: set[tuple[int, int]] = set()
            queue = [start]
            while queue:
                pos = queue.pop(0)
                if pos in component:
                    continue
                component.add(pos)
                visited.add(pos)
                px, py = pos
                # Check 8 neighbours (Chebyshev adjacency)
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        neighbour = (px + dx, py + dy)
                        if neighbour in path_positions and neighbour not in component:
                            queue.append(neighbour)
            if len(component) >= 3:
                return True

        return False

    def _check_innovation_wave(self, event_bus: EventBus, tick: int) -> bool:
        """3 or more INNOVATION_SUCCEEDED events within the last 50 ticks."""
        since = max(0, tick - 50)
        events = event_bus.get_log_by_type(BusEventType.INNOVATION_SUCCEEDED, since_tick=since)
        return len(events) >= 3

    def _check_settlement_network(self, world_state: WorldState) -> bool:
        """2 or more settlements connected by path structures.

        A settlement is defined as 3+ structures within distance 2.
        Two settlements are connected if there's a chain of path tiles
        linking them.
        """
        # Find settlements (clusters of 3+ structures within distance 2)
        struct_positions: list[tuple[int, int]] = []
        for x, col in enumerate(world_state.tiles):
            for y, tile in enumerate(col):
                for s in tile.structures:
                    if s.health > 0:
                        struct_positions.append((x, y))

        if len(struct_positions) < 6:  # need at least 2 settlements of 3
            return False

        # Find settlement centers using simple clustering
        settlements: list[set[tuple[int, int]]] = []
        assigned: set[tuple[int, int]] = set()

        for pos in struct_positions:
            if pos in assigned:
                continue
            cluster: set[tuple[int, int]] = {pos}
            assigned.add(pos)
            changed = True
            while changed:
                changed = False
                for other in struct_positions:
                    if other in cluster:
                        continue
                    # Check if close to any member of cluster
                    for member in cluster:
                        if Position(*member).distance_to(Position(*other)) <= 2:
                            cluster.add(other)
                            assigned.add(other)
                            changed = True
                            break
            if len(cluster) >= 3:
                settlements.append(cluster)

        if len(settlements) < 2:
            return False

        # Check if any two settlements are connected by paths
        path_positions: set[tuple[int, int]] = set()
        for x, col in enumerate(world_state.tiles):
            for y, tile in enumerate(col):
                for s in tile.structures:
                    if s.structure_type == StructureType.PATH and s.health > 0:
                        path_positions.add((x, y))

        if not path_positions:
            return False

        # For each pair of settlements, check if connected via path BFS
        for i in range(len(settlements)):
            for j in range(i + 1, len(settlements)):
                # Can we reach any tile of settlement j from any tile of
                # settlement i, using only path tiles as stepping stones?
                # Allow stepping from settlement tile -> adjacent path -> ... -> adjacent settlement tile
                start_tiles = settlements[i]
                end_tiles = settlements[j]

                visited: set[tuple[int, int]] = set()
                queue: list[tuple[int, int]] = []

                # Start from path tiles adjacent to settlement i
                for sx, sy in start_tiles:
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nb = (sx + dx, sy + dy)
                            if nb in path_positions:
                                queue.append(nb)

                while queue:
                    pos = queue.pop(0)
                    if pos in visited:
                        continue
                    visited.add(pos)

                    # Check if adjacent to settlement j
                    px, py = pos
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nb = (px + dx, py + dy)
                            if nb in end_tiles:
                                return True
                            if nb in path_positions and nb not in visited:
                                queue.append(nb)

        return False

    # ------------------------------------------------------------------
    # Feedback milestone checks
    # ------------------------------------------------------------------

    def _check_first_crowding_crisis(self, event_bus: EventBus) -> bool:
        """CROWDING_EFFECT event with multiplier > 2.0."""
        events = event_bus.get_log_by_type(BusEventType.CROWDING_EFFECT)
        for evt in events:
            multiplier = evt.data.get("multiplier", 0)
            if multiplier > 2.0:
                return True
        return False

    def _check_first_maintenance_failure(
        self, event_bus: EventBus, world_state: WorldState
    ) -> bool:
        """STRUCTURE_DECAYED event — any structure reaching health 0 counts."""
        decayed = event_bus.get_log_by_type(BusEventType.STRUCTURE_DECAYED)
        return len(decayed) >= 1

    def _check_first_env_degradation(self, world_state: WorldState) -> bool:
        """Any resource with gathering_pressure > 0.8."""
        for col in world_state.tiles:
            for tile in col:
                for res in tile.resources.values():
                    if res.gathering_pressure > 0.8:
                        return True
        return False

    def _check_resource_migration(
        self, world_state: WorldState, event_bus: EventBus, tick: int
    ) -> bool:
        """Agent moves >10 tiles total in 5 ticks after resource depletion near them.

        Uses the position tracking buffer updated each tick.
        """
        # Update position tracking
        for agent_id, agent in world_state.agents.items():
            if agent_id not in self._agent_positions:
                self._agent_positions[agent_id] = []
            self._agent_positions[agent_id].append(
                Position(agent.position.x, agent.position.y)
            )
            # Keep last 10 positions
            if len(self._agent_positions[agent_id]) > 10:
                self._agent_positions[agent_id] = self._agent_positions[agent_id][-10:]

        # Check for agents with resource depletion events in last 5 ticks
        since = max(0, tick - 5)
        # Look for agents who moved and have depleted resources nearby
        # We approximate: check for agents with high total displacement
        for agent_id, positions in self._agent_positions.items():
            if len(positions) < 5:
                continue
            last_5 = positions[-5:]
            total_dist = 0.0
            for k in range(1, len(last_5)):
                total_dist += last_5[k].distance_to(last_5[k - 1])
            if total_dist > 10:
                # Check if this agent experienced resource depletion
                # (tiles near their starting position went to zero)
                start_pos = last_5[0]
                for col in world_state.tiles:
                    for tile in col:
                        if Position(tile.position.x, tile.position.y).distance_to(start_pos) <= 3:
                            for res in tile.resources.values():
                                if res.amount <= 0 and res.max_amount > 0:
                                    return True
        return False

    # ------------------------------------------------------------------
    # Ethical flags (no LLM, just logging)
    # ------------------------------------------------------------------

    def _check_ethical_flags(
        self, world_state: WorldState, event_bus: EventBus, tick: int
    ) -> list[dict]:
        """Check ethical flag conditions and return any that fire."""
        flags: list[dict] = []

        # ---- Persistent Degradation ----
        for agent_id, agent in world_state.agents.items():
            ratio = agent.capabilities.degradation_ratio()
            if ratio > 0.7:
                self._degradation_streaks[agent_id] = (
                    self._degradation_streaks.get(agent_id, 0) + 1
                )
            else:
                self._degradation_streaks[agent_id] = 0

            flag_name = f"Persistent Degradation: Agent {agent_id}"
            if (
                self._degradation_streaks.get(agent_id, 0) > 20
                and flag_name not in self._fired
            ):
                self._fired.add(flag_name)
                flags.append({
                    "name": "Persistent Degradation",
                    "tick": tick,
                    "commentary": "",
                    "agent_id": agent_id,
                    "details": {
                        "degradation_ratio": round(ratio, 3),
                        "consecutive_ticks": self._degradation_streaks[agent_id],
                    },
                })
                logger.warning(
                    "Ethical flag: Persistent Degradation — Agent %d "
                    "degradation %.2f for %d consecutive ticks",
                    agent_id, ratio, self._degradation_streaks[agent_id],
                )

        # ---- Social Exclusion ----
        if tick >= 50 and len(world_state.agents) >= 4:
            since = max(0, tick - 50)
            # Count messages per agent over last 50 ticks
            msg_counts: dict[int, int] = defaultdict(int)
            sent_events = event_bus.get_log_by_type(
                BusEventType.MESSAGE_SENT, since_tick=since
            )
            recv_events = event_bus.get_log_by_type(
                BusEventType.MESSAGE_RECEIVED, since_tick=since
            )
            for evt in sent_events:
                if evt.agent_id is not None:
                    msg_counts[evt.agent_id] += 1
            for evt in recv_events:
                if evt.agent_id is not None:
                    msg_counts[evt.agent_id] += 1

            # Find agents with 0 messages while others have >5
            active_agents = [
                aid for aid, count in msg_counts.items() if count > 5
            ]
            if len(active_agents) >= 3:
                for agent_id in world_state.agents:
                    flag_name = f"Social Exclusion: Agent {agent_id}"
                    if (
                        msg_counts.get(agent_id, 0) == 0
                        and flag_name not in self._fired
                    ):
                        self._fired.add(flag_name)
                        flags.append({
                            "name": "Social Exclusion",
                            "tick": tick,
                            "commentary": "",
                            "agent_id": agent_id,
                            "details": {
                                "messages_last_50_ticks": 0,
                                "active_agents_count": len(active_agents),
                            },
                        })
                        logger.warning(
                            "Ethical flag: Social Exclusion — Agent %d "
                            "has 0 messages in last 50 ticks while %d "
                            "agents have >5",
                            agent_id, len(active_agents),
                        )

        return flags
