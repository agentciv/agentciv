"""Per-tick data aggregation for the Watcher.

No LLM calls — pure computation. Produces a structured dict summarising
everything that happened during a single simulation tick.
"""

from __future__ import annotations

from src.types import (
    BusEventType,
    EventBus,
    StructureType,
    WorldState,
)
from src.engine.feedback import effective_regeneration_rate
from src.config import SimulationConfig


def generate_tick_report(
    world_state: WorldState,
    event_bus: EventBus,
    tick: int,
    config: SimulationConfig,
) -> dict:
    """Build a structured summary of the simulation at the given tick.

    Uses the event bus log for per-tick event counts and the world state
    for aggregate statistics. All numbers are rounded for readability.

    Returns:
        A dict with keys: population, resources, structures,
        communication, composition, innovation, specialisation,
        rules, feedback, environment.
    """
    agents = world_state.agents

    # ---- helpers: event counts for this tick ----
    def _count(event_type: BusEventType) -> int:
        return len(event_bus.get_log_by_type(event_type, since_tick=tick))

    def _events(event_type: BusEventType) -> list:
        return event_bus.get_log_by_type(event_type, since_tick=tick)

    # ==================================================================
    # Population
    # ==================================================================
    num_agents = len(agents)
    avg_wellbeing = (
        sum(a.wellbeing for a in agents.values()) / num_agents
        if num_agents > 0
        else 0.0
    )
    avg_degradation = (
        sum(a.capabilities.degradation_ratio() for a in agents.values()) / num_agents
        if num_agents > 0
        else 0.0
    )
    critical_agents = sum(
        1 for a in agents.values() if a.needs.any_critical()
    )

    population = {
        "total": num_agents,
        "avg_wellbeing": round(avg_wellbeing, 3),
        "avg_degradation_ratio": round(avg_degradation, 3),
        "agents_with_critical_needs": critical_agents,
    }

    # ==================================================================
    # Resources
    # ==================================================================
    resource_totals: dict[str, float] = {}
    tiles_at_zero: dict[str, int] = {}

    for col in world_state.tiles:
        for tile in col:
            for rtype, res in tile.resources.items():
                resource_totals[rtype] = resource_totals.get(rtype, 0.0) + res.amount
                if res.amount <= 0:
                    tiles_at_zero[rtype] = tiles_at_zero.get(rtype, 0) + 1

    resources = {
        "total_available": {k: round(v, 2) for k, v in resource_totals.items()},
        "tiles_at_zero": tiles_at_zero,
    }

    # ==================================================================
    # Structures
    # ==================================================================
    structure_counts: dict[str, int] = {}
    custom_named_count = 0
    all_structures = []

    for col in world_state.tiles:
        for tile in col:
            for s in tile.structures:
                if s.health > 0:
                    stype = s.structure_type.value
                    structure_counts[stype] = structure_counts.get(stype, 0) + 1
                    if s.custom_name:
                        custom_named_count += 1
                    all_structures.append(s)

    built_events = _events(BusEventType.STRUCTURE_BUILT)
    decayed_events = _events(BusEventType.STRUCTURE_DECAYED)

    structures = {
        "count_by_type": structure_counts,
        "total": sum(structure_counts.values()),
        "custom_named": custom_named_count,
        "built_this_tick": len(built_events),
        "decayed_this_tick": len(decayed_events),
    }

    # ==================================================================
    # Communication
    # ==================================================================
    msg_events = _events(BusEventType.MESSAGE_SENT)
    unique_pairs: set[tuple[int, int]] = set()
    broadcast_count = 0
    for evt in msg_events:
        sender = evt.data.get("sender_id")
        receiver = evt.data.get("receiver_id")
        if receiver == -1:
            broadcast_count += 1
        elif sender is not None and receiver is not None:
            pair = (min(sender, receiver), max(sender, receiver))
            unique_pairs.add(pair)

    communication = {
        "messages_sent": len(msg_events),
        "unique_pairs": len(unique_pairs),
        "broadcasts": broadcast_count,
    }

    # ==================================================================
    # Composition
    # ==================================================================
    comp_discovered = _count(BusEventType.COMPOSITION_DISCOVERED)
    comp_failed = _count(BusEventType.COMPOSITION_FAILED)

    composition = {
        "attempted": comp_discovered + comp_failed,
        "succeeded": comp_discovered,
        "failed": comp_failed,
        "total_recipes": len(world_state.discovered_recipes),
    }

    # ==================================================================
    # Innovation
    # ==================================================================
    innov_succeeded = _count(BusEventType.INNOVATION_SUCCEEDED)
    innov_failed = _count(BusEventType.INNOVATION_FAILED)

    innovation = {
        "attempted": innov_succeeded + innov_failed,
        "succeeded": innov_succeeded,
        "failed": innov_failed,
        "total_innovations": custom_named_count,  # custom_name implies innovation or composition
    }

    # ==================================================================
    # Specialisation
    # ==================================================================
    spec_events = _events(BusEventType.SPECIALISATION_GAINED)
    spec_distribution: dict[str, int] = {}
    for agent in agents.values():
        for spec in agent.specialisations:
            spec_distribution[spec] = spec_distribution.get(spec, 0) + 1

    specialisation = {
        "new_this_tick": len(spec_events),
        "distribution": spec_distribution,
    }

    # ==================================================================
    # Rules
    # ==================================================================
    rule_proposed = _count(BusEventType.RULE_PROPOSED)
    rule_accepted = _count(BusEventType.RULE_ACCEPTED)
    rule_established = _count(BusEventType.RULE_ESTABLISHED)

    active_rules = [r for r in world_state.collective_rules if r.established]
    all_rules = world_state.collective_rules
    avg_adoption = (
        sum(r.adoption_rate for r in all_rules) / len(all_rules)
        if all_rules
        else 0.0
    )

    rules = {
        "proposed_this_tick": rule_proposed,
        "accepted_this_tick": rule_accepted,
        "newly_established": rule_established,
        "total_active": len(active_rules),
        "total_proposed": len(all_rules),
        "avg_adoption_rate": round(avg_adoption, 3),
    }

    # ==================================================================
    # Feedback loops
    # ==================================================================
    crowding_events = _events(BusEventType.CROWDING_EFFECT)
    maintenance_events = _events(BusEventType.MAINTENANCE_CONSUMED)

    tiles_high_pressure = 0
    for col in world_state.tiles:
        for tile in col:
            for res in tile.resources.values():
                if res.gathering_pressure > 0.5:
                    tiles_high_pressure += 1
                    break  # count tile once

    feedback = {
        "crowding_events": len(crowding_events),
        "maintenance_consumed": len(maintenance_events),
        "tiles_high_gathering_pressure": tiles_high_pressure,
    }

    # ==================================================================
    # Environment
    # ==================================================================
    total_eff_regen = 0.0
    total_base_regen = 0.0
    resource_count = 0

    for col in world_state.tiles:
        for tile in col:
            for res in tile.resources.values():
                total_base_regen += res.regeneration_rate
                total_eff_regen += effective_regeneration_rate(res, tile, config)
                resource_count += 1

    avg_base = total_base_regen / resource_count if resource_count > 0 else 0.0
    avg_eff = total_eff_regen / resource_count if resource_count > 0 else 0.0

    environment = {
        "avg_base_regen": round(avg_base, 5),
        "avg_effective_regen": round(avg_eff, 5),
    }

    return {
        "tick": tick,
        "population": population,
        "resources": resources,
        "structures": structures,
        "communication": communication,
        "composition": composition,
        "innovation": innovation,
        "specialisation": specialisation,
        "rules": rules,
        "feedback": feedback,
        "environment": environment,
    }
