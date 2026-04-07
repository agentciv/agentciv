"""Emergence metrics extraction from simulation state.

Computes quantifiable metrics from a WorldState snapshot,
enabling automated comparison across different configurations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..types import BusEvent, BusEventType, WorldState


@dataclass
class EmergenceScore:
    """Quantified emergence metrics from a simulation run."""

    # Innovation
    innovation_count: int = 0
    innovation_types: list[str] = field(default_factory=list)
    composition_count: int = 0

    # Built environment
    structure_count: int = 0
    unique_structure_types: int = 0

    # Social network
    relationship_count: int = 0
    bonded_pairs: int = 0
    avg_relationship_strength: float = 0.0
    network_density: float = 0.0

    # Governance
    rules_proposed: int = 0
    rules_established: int = 0

    # Population wellbeing
    avg_wellbeing: float = 0.0
    avg_curiosity: float = 0.0
    population_count: int = 0

    # Maslow distribution (level -> count)
    maslow_distribution: dict[int, int] = field(default_factory=dict)
    avg_maslow_level: float = 0.0

    # Specialisation
    total_specialisations: int = 0
    agents_with_specialisation: int = 0

    # Communication
    total_messages: int = 0

    # Cooperation (from event bus)
    cooperation_events: int = 0
    resource_sharing_events: int = 0

    # Composite score (0-1)
    composite_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a flat dictionary."""
        return {
            "innovation_count": self.innovation_count,
            "innovation_types": self.innovation_types,
            "composition_count": self.composition_count,
            "structure_count": self.structure_count,
            "unique_structure_types": self.unique_structure_types,
            "relationship_count": self.relationship_count,
            "bonded_pairs": self.bonded_pairs,
            "avg_relationship_strength": round(self.avg_relationship_strength, 3),
            "network_density": round(self.network_density, 3),
            "rules_proposed": self.rules_proposed,
            "rules_established": self.rules_established,
            "avg_wellbeing": round(self.avg_wellbeing, 3),
            "avg_curiosity": round(self.avg_curiosity, 3),
            "population_count": self.population_count,
            "maslow_distribution": self.maslow_distribution,
            "avg_maslow_level": round(self.avg_maslow_level, 2),
            "total_specialisations": self.total_specialisations,
            "agents_with_specialisation": self.agents_with_specialisation,
            "total_messages": self.total_messages,
            "cooperation_events": self.cooperation_events,
            "resource_sharing_events": self.resource_sharing_events,
            "composite_score": round(self.composite_score, 4),
        }


def compute_emergence(
    world_state: WorldState,
    bus_events: list[BusEvent] | None = None,
) -> EmergenceScore:
    """Compute emergence metrics from a world state snapshot.

    Args:
        world_state: The final (or current) world state.
        bus_events: Optional list of bus events for richer metrics.
            If not provided, only state-based metrics are computed.

    Returns:
        EmergenceScore with all metrics populated.
    """
    score = EmergenceScore()
    agents = list(world_state.agents.values())
    n_agents = len(agents)

    if n_agents == 0:
        return score

    score.population_count = n_agents

    # ── Innovation ──
    score.innovation_count = len(world_state.discovered_recipes)
    score.innovation_types = [r.output_name for r in world_state.discovered_recipes]
    score.composition_count = sum(
        r.times_built for r in world_state.discovered_recipes
    )

    # ── Built environment ──
    structure_types = set()
    total_structures = 0
    for col in world_state.tiles:
        for tile in col:
            for s in tile.structures:
                total_structures += 1
                name = s.custom_name or s.structure_type.value
                structure_types.add(name)
    score.structure_count = total_structures
    score.unique_structure_types = len(structure_types)

    # ── Social network ──
    total_relationships = 0
    total_strength = 0.0
    bonded = 0
    for agent in agents:
        for rel in agent.relationships.values():
            total_relationships += 1
            total_strength += rel.positive_count
            if rel.is_bonded:
                bonded += 1

    # Relationships are directional, so count each pair once
    score.relationship_count = total_relationships
    score.bonded_pairs = bonded // 2  # each bond counted from both sides
    if total_relationships > 0:
        score.avg_relationship_strength = total_strength / total_relationships
    # Network density: actual edges / possible edges
    possible_edges = n_agents * (n_agents - 1)
    if possible_edges > 0:
        score.network_density = total_relationships / possible_edges

    # ── Governance ──
    score.rules_proposed = len(world_state.collective_rules)
    score.rules_established = sum(
        1 for r in world_state.collective_rules if r.established
    )

    # ── Wellbeing & curiosity ──
    score.avg_wellbeing = sum(a.wellbeing for a in agents) / n_agents
    score.avg_curiosity = sum(a.curiosity for a in agents) / n_agents

    # ── Maslow distribution ──
    maslow_dist: dict[int, int] = {}
    maslow_sum = 0
    for agent in agents:
        level = agent.maslow_level
        maslow_dist[level] = maslow_dist.get(level, 0) + 1
        maslow_sum += level
    score.maslow_distribution = maslow_dist
    score.avg_maslow_level = maslow_sum / n_agents

    # ── Specialisation ──
    total_specs = 0
    agents_specialised = 0
    for agent in agents:
        if agent.specialisations:
            agents_specialised += 1
            total_specs += len(agent.specialisations)
    score.total_specialisations = total_specs
    score.agents_with_specialisation = agents_specialised

    # ── Communication ──
    score.total_messages = len(world_state.message_log)

    # ── Event-bus metrics (cooperation, resource sharing) ──
    if bus_events:
        for event in bus_events:
            if event.type == BusEventType.RESOURCE_GIVEN:
                score.resource_sharing_events += 1
                score.cooperation_events += 1

    # ── Composite score ──
    score.composite_score = _compute_composite(score)

    return score


def _compute_composite(s: EmergenceScore) -> float:
    """Compute a weighted composite emergence score (0-1).

    Weights reflect which aspects of emergence are most significant:
    - Innovation and composition: high weight (novel behaviour)
    - Governance: high weight (institutional emergence)
    - Social network: medium weight (relationship complexity)
    - Maslow progression: medium weight (development trajectory)
    - Wellbeing: lower weight (outcome, not process)
    """
    if s.population_count == 0:
        return 0.0

    components: list[tuple[float, float]] = []  # (value, weight)

    # Innovation (0-1, capped at 10 innovations = 1.0)
    innovation_norm = min(1.0, s.innovation_count / 10)
    components.append((innovation_norm, 0.20))

    # Governance (0-1, any established rule is significant)
    governance_norm = min(1.0, s.rules_established / 3)
    components.append((governance_norm, 0.15))

    # Social network density (already 0-1)
    components.append((s.network_density, 0.15))

    # Bonded pairs (0-1, capped at half the population being bonded)
    max_pairs = s.population_count // 2
    bond_norm = min(1.0, s.bonded_pairs / max(1, max_pairs))
    components.append((bond_norm, 0.10))

    # Maslow progression (normalised to 0-1, level 8 is max)
    maslow_norm = (s.avg_maslow_level - 1) / 7 if s.avg_maslow_level > 1 else 0.0
    components.append((maslow_norm, 0.15))

    # Specialisation (0-1, capped at 80% of agents specialised)
    spec_norm = min(1.0, s.agents_with_specialisation / max(1, int(s.population_count * 0.8)))
    components.append((spec_norm, 0.10))

    # Communication density (normalised per agent per tick, capped)
    # Rough normalisation: 2 messages per agent = good communication
    msg_norm = min(1.0, s.total_messages / max(1, s.population_count * 2))
    components.append((msg_norm, 0.10))

    # Cooperation (resource sharing)
    coop_norm = min(1.0, s.resource_sharing_events / max(1, s.population_count))
    components.append((coop_norm, 0.05))

    total_weight = sum(w for _, w in components)
    weighted_sum = sum(v * w for v, w in components)

    return weighted_sum / total_weight if total_weight > 0 else 0.0
