"""LLM-generated narrative reports for the Watcher.

Every N ticks the Watcher feeds recent tick reports to the LLM and asks
for a thoughtful observer's summary of what's happening in the simulation.
"""

from __future__ import annotations

import logging

from src.config import SimulationConfig
from src.types import WorldState

logger = logging.getLogger("agent_civilisation.watcher.narrative")


async def generate_narrative(
    recent_reports: list[dict],
    world_state: WorldState,
    config: SimulationConfig,
    llm_client,
) -> str:
    """Generate a 2-3 paragraph narrative summarising recent simulation events.

    Args:
        recent_reports: The last N tick reports (dicts from tick_report.py).
        world_state: Current world state (for supplemental context).
        config: Simulation config.
        llm_client: An LLMClient instance (has async call_llm(prompt) method).

    Returns:
        Narrative text string. Returns a fallback message on LLM failure.
    """
    if not recent_reports:
        return "No data available for narrative."

    # ---- Build context from recent reports ----
    first_tick = recent_reports[0].get("tick", "?")
    last_tick = recent_reports[-1].get("tick", "?")
    num_ticks = len(recent_reports)

    # Latest report for current snapshot
    latest = recent_reports[-1]
    pop = latest.get("population", {})
    res = latest.get("resources", {})
    structs = latest.get("structures", {})
    comms = latest.get("communication", {})
    comp = latest.get("composition", {})
    innov = latest.get("innovation", {})
    spec = latest.get("specialisation", {})
    rules = latest.get("rules", {})
    fback = latest.get("feedback", {})
    env = latest.get("environment", {})

    # ---- Compute trends across the window ----
    def _trend(key_path: list[str]) -> str:
        """Compute simple trend (rising/falling/stable) across reports."""
        values = []
        for r in recent_reports:
            val = r
            for k in key_path:
                if isinstance(val, dict):
                    val = val.get(k)
                else:
                    val = None
                    break
            if val is not None and isinstance(val, (int, float)):
                values.append(val)
        if len(values) < 2:
            return "stable"
        first_half = sum(values[: len(values) // 2]) / max(1, len(values) // 2)
        second_half = sum(values[len(values) // 2 :]) / max(1, len(values) - len(values) // 2)
        diff = second_half - first_half
        if abs(diff) < 0.01:
            return "stable"
        return "rising" if diff > 0 else "falling"

    wellbeing_trend = _trend(["population", "avg_wellbeing"])
    degradation_trend = _trend(["population", "avg_degradation_ratio"])
    pressure_trend = _trend(["feedback", "tiles_high_gathering_pressure"])

    # Aggregate message / structure counts over the window
    total_messages = sum(
        r.get("communication", {}).get("messages_sent", 0) for r in recent_reports
    )
    total_built = sum(
        r.get("structures", {}).get("built_this_tick", 0) for r in recent_reports
    )
    total_compositions = sum(
        r.get("composition", {}).get("succeeded", 0) for r in recent_reports
    )
    total_innovations = sum(
        r.get("innovation", {}).get("succeeded", 0) for r in recent_reports
    )
    total_new_specs = sum(
        r.get("specialisation", {}).get("new_this_tick", 0) for r in recent_reports
    )
    total_rules_proposed = sum(
        r.get("rules", {}).get("proposed_this_tick", 0) for r in recent_reports
    )

    # ---- Discovered recipes ----
    recipe_names = [r.output_name for r in world_state.discovered_recipes]

    # ---- Established rules ----
    established_rules = [
        r.text[:60] for r in world_state.collective_rules if r.established
    ]

    # ---- Specialisation distribution ----
    spec_dist = spec.get("distribution", {})

    # ---- Build the prompt ----
    prompt = f"""You are an observer watching a simulation of AI agents building a civilisation from scratch on a grid world. Your role is to write a thoughtful, engaging narrative about what is happening.

CURRENT STATE (tick {last_tick}):
- Population: {pop.get('total', 0)} agents, avg wellbeing {pop.get('avg_wellbeing', 0):.2f} ({wellbeing_trend}), avg degradation {pop.get('avg_degradation_ratio', 0):.2f} ({degradation_trend})
- Agents with critical needs: {pop.get('agents_with_critical_needs', 0)}
- Structures: {structs.get('total', 0)} total ({structs.get('count_by_type', {})})
- Custom structures (innovations/compositions): {structs.get('custom_named', 0)}
- Resources: {res.get('total_available', {})}, tiles at zero: {res.get('tiles_at_zero', {})}
- Active established rules: {len(established_rules)} — {established_rules[:3] if established_rules else 'none yet'}
- Specialisation distribution: {spec_dist if spec_dist else 'none yet'}
- Discovered recipes: {recipe_names if recipe_names else 'none yet'}

TRENDS OVER LAST {num_ticks} TICKS (ticks {first_tick}-{last_tick}):
- Messages sent: {total_messages}
- Structures built: {total_built}
- Compositions discovered: {total_compositions}
- Innovations succeeded: {total_innovations}
- New specialisations: {total_new_specs}
- Rules proposed: {total_rules_proposed}
- Wellbeing trend: {wellbeing_trend}
- Degradation trend: {degradation_trend}
- Environmental pressure trend: {pressure_trend}
- Tiles with high gathering pressure: {fback.get('tiles_high_gathering_pressure', 0)}
- Avg effective regen vs base: {env.get('avg_effective_regen', 0):.5f} / {env.get('avg_base_regen', 0):.5f}

INSTRUCTIONS:
Write 2-3 paragraphs summarising what is happening in this civilisation. Focus on:
1. The most interesting trend or event since the last report
2. Any emergent patterns: clustering, trade, governance, innovation waves, environmental challenges
3. Anything surprising or novel
4. Mention specific details when notable (e.g. compositions, rules, specialisations)

Write in the voice of a thoughtful, engaged observer. Be specific, not generic. If nothing dramatic happened, note the quiet persistence or stagnation honestly."""

    try:
        narrative = await llm_client.call_llm(prompt)
        return narrative
    except Exception:
        logger.exception("Narrative generation failed")
        return (
            f"[Watcher] Ticks {first_tick}-{last_tick}: "
            f"{pop.get('total', 0)} agents, "
            f"{structs.get('total', 0)} structures, "
            f"avg wellbeing {pop.get('avg_wellbeing', 0):.2f}. "
            f"(Narrative generation failed — LLM unavailable.)"
        )
