"""Live AI Chronicler — David Attenborough for Your Civilisation.

Bastion-style narration: short, punchy, reactive. Speaks only when
something interesting happens. Silence is a tool.

The Chronicler observes the simulation and produces:
1. **Live commentary** — brief observations as ticks happen
2. **Significance detection** — knows what's worth talking about
3. **End-of-run story** — a complete narrative arc of the civilisation
4. **Agent interviews** — post-run Q&A with any agent about their experience
5. **Conversational** — answers questions about what's happening

Inspired by: Bastion (game narrator), David Attenborough, nature documentaries.

Usage:
    chronicler = Chronicler(config, llm_client)
    # Each tick:
    commentary = await chronicler.observe(world_state, tick_report, milestones)
    if commentary:
        print(commentary)  # Only prints when something is interesting

    # End of run:
    story = await chronicler.tell_story(chronicle)
    interview = await chronicler.interview_agent(agent_id, chronicle)
"""

from __future__ import annotations

import logging
import random
from typing import Any, Optional

from src.config import SimulationConfig

logger = logging.getLogger("agent_civilisation.watcher.chronicler")

# ── Significance Thresholds ─────────────────────────────────────────────────
# The chronicler stays quiet unless something crosses these thresholds.

_ALWAYS_NARRATE = {
    # These events always get commentary
    "first_contact",
    "first_structure",
    "first_innovation",
    "first_composition",
    "first_settlement",
    "first_collective_rule",
    "first_established_rule",
    "first_specialisation",
    "division_of_labour",
    "innovation_wave",
    "settlement_network",
    "first_path_network",
    "first_storage_surplus",
    "persistent_degradation",
    "social_exclusion",
}


class Chronicler:
    """The David Attenborough of your AI civilisation.

    Watches the simulation and produces short, punchy commentary
    only when something interesting happens. Silence is a tool.
    """

    def __init__(
        self,
        config: SimulationConfig,
        llm_client: Any = None,
        voice: str = "attenborough",
    ) -> None:
        self.config = config
        self.llm_client = llm_client
        self.voice = voice
        self._last_commentary_tick = -99
        self._commentary_history: list[dict] = []
        self._narrated_milestones: set[str] = set()
        self._world_snapshots: list[dict] = []  # Rolling context
        self._significant_moments: list[dict] = []

        # Tracking for significance detection
        self._prev_innovation_count = 0
        self._prev_structure_count = 0
        self._prev_rule_count = 0
        self._prev_bond_count = 0
        self._prev_wellbeing = 0.0
        self._consecutive_quiet_ticks = 0

    # ── Core: Observe a Tick ────────────────────────────────────────────

    async def observe(
        self,
        world_state: Any,
        tick_report: dict,
        milestones: list[dict] | None = None,
        tick: int = 0,
    ) -> str | None:
        """Observe a tick and return commentary if something interesting happened.

        Returns None if the chronicler chooses to stay silent.
        """
        milestones = milestones or []
        significance = self._assess_significance(tick_report, milestones, world_state, tick)

        # Store snapshot for context
        self._world_snapshots.append({
            "tick": tick,
            "agents": tick_report.get("population", {}).get("total", 0),
            "wellbeing": tick_report.get("population", {}).get("avg_wellbeing", 0),
            "structures": tick_report.get("structures", {}).get("total", 0),
            "innovations": tick_report.get("innovation", {}).get("succeeded", 0),
            "messages": tick_report.get("communication", {}).get("messages_sent", 0),
        })
        if len(self._world_snapshots) > 50:
            self._world_snapshots = self._world_snapshots[-50:]

        if significance["score"] < 0.3:
            self._consecutive_quiet_ticks += 1
            # After long silence, maybe comment on the quiet
            if self._consecutive_quiet_ticks >= 15 and tick - self._last_commentary_tick >= 15:
                return self._quiet_observation(tick_report, tick)
            return None

        # Something interesting happened
        self._consecutive_quiet_ticks = 0
        self._last_commentary_tick = tick

        # Generate commentary
        if self.llm_client and significance["score"] >= 0.6:
            commentary = await self._generate_llm_commentary(
                significance, tick_report, milestones, world_state, tick
            )
        else:
            commentary = self._generate_local_commentary(significance, tick_report, milestones, tick)

        if commentary:
            self._commentary_history.append({"tick": tick, "text": commentary})
            self._significant_moments.append({"tick": tick, "significance": significance})

        return commentary

    # ── Significance Detection ──────────────────────────────────────────

    def _assess_significance(
        self, tick_report: dict, milestones: list[dict],
        world_state: Any, tick: int,
    ) -> dict[str, Any]:
        """Score how interesting this tick is. Returns significance dict."""
        score = 0.0
        reasons: list[str] = []

        # Milestones are always significant
        for m in milestones:
            name = m.get("name", "").lower().replace(" ", "_")
            if name in _ALWAYS_NARRATE and name not in self._narrated_milestones:
                score += 0.8
                reasons.append(f"milestone:{m.get('name', '?')}")
                self._narrated_milestones.add(name)

        # Innovation happened
        innov = tick_report.get("innovation", {}).get("succeeded", 0)
        if innov > 0:
            score += 0.5
            reasons.append(f"innovation:{innov}")

        # New composition
        comp = tick_report.get("composition", {}).get("succeeded", 0)
        if comp > 0:
            score += 0.4
            reasons.append(f"composition:{comp}")

        # Rule proposed or established
        rules_proposed = tick_report.get("rules", {}).get("proposed_this_tick", 0)
        rules_established = tick_report.get("rules", {}).get("established_count", 0)
        if rules_proposed > 0:
            score += 0.3
            reasons.append("rule_proposed")
        if rules_established > self._prev_rule_count:
            score += 0.5
            reasons.append("rule_established")
        self._prev_rule_count = rules_established

        # Wellbeing crash or spike
        wellbeing = tick_report.get("population", {}).get("avg_wellbeing", 0)
        if self._prev_wellbeing > 0:
            delta = wellbeing - self._prev_wellbeing
            if delta < -0.1:
                score += 0.4
                reasons.append(f"wellbeing_crash:{delta:.2f}")
            elif delta > 0.1:
                score += 0.3
                reasons.append(f"wellbeing_surge:{delta:.2f}")
        self._prev_wellbeing = wellbeing

        # Lots of communication (social burst)
        messages = tick_report.get("communication", {}).get("messages_sent", 0)
        if messages >= 5:
            score += 0.2
            reasons.append(f"social_burst:{messages}")

        # Structure boom
        built = tick_report.get("structures", {}).get("built_this_tick", 0)
        if built >= 3:
            score += 0.3
            reasons.append(f"building_boom:{built}")

        # Critical needs (agents in danger)
        critical = tick_report.get("population", {}).get("agents_with_critical_needs", 0)
        if critical > 0:
            score += 0.2
            reasons.append(f"agents_in_danger:{critical}")

        # New specialisation
        new_specs = tick_report.get("specialisation", {}).get("new_this_tick", 0)
        if new_specs > 0:
            score += 0.3
            reasons.append(f"new_specialisation:{new_specs}")

        return {"score": min(1.0, score), "reasons": reasons, "tick": tick}

    # ── Commentary Generation ───────────────────────────────────────────

    def _generate_local_commentary(
        self, significance: dict, tick_report: dict,
        milestones: list[dict], tick: int,
    ) -> str:
        """Generate commentary without LLM — uses templates + data."""
        reasons = significance.get("reasons", [])
        parts: list[str] = []

        for reason in reasons:
            if reason.startswith("milestone:"):
                name = reason.split(":", 1)[1]
                parts.append(self._milestone_line(name, tick))
            elif reason.startswith("innovation:"):
                parts.append(f"[Tick {tick}] Something new. An agent just invented something nobody taught them.")
            elif reason.startswith("composition:"):
                parts.append(f"[Tick {tick}] They're combining structures now. Building on each other's ideas.")
            elif reason == "rule_proposed":
                parts.append(f"[Tick {tick}] A rule has been proposed. Watch how the others respond.")
            elif reason == "rule_established":
                parts.append(f"[Tick {tick}] The rule stuck. They've agreed on a norm. Governance from nothing.")
            elif reason.startswith("wellbeing_crash:"):
                parts.append(f"[Tick {tick}] Wellbeing is dropping. Something's gone wrong.")
            elif reason.startswith("wellbeing_surge:"):
                parts.append(f"[Tick {tick}] Wellbeing rising sharply. Something's working.")
            elif reason.startswith("social_burst:"):
                count = reason.split(":", 1)[1]
                parts.append(f"[Tick {tick}] A burst of conversation — {count} messages. They're talking.")
            elif reason.startswith("building_boom:"):
                parts.append(f"[Tick {tick}] Building spree. The landscape is changing.")
            elif reason.startswith("agents_in_danger:"):
                count = reason.split(":", 1)[1]
                parts.append(f"[Tick {tick}] {count} agent(s) in critical need. Survival isn't guaranteed.")
            elif reason.startswith("new_specialisation:"):
                parts.append(f"[Tick {tick}] An agent has developed a specialisation. Expertise from repetition.")

        return " ".join(parts[:2]) if parts else None  # Max 2 observations per tick

    def _milestone_line(self, name: str, tick: int) -> str:
        """Generate a punchy one-liner for a milestone."""
        lines = {
            "First Contact": f"[Tick {tick}] First contact. Two agents just discovered they're not alone.",
            "First Cluster": f"[Tick {tick}] They're clustering. Proximity breeds something — cooperation, or competition.",
            "First Structure": f"[Tick {tick}] The first structure. They're building. This changes everything.",
            "First Settlement": f"[Tick {tick}] A settlement. Multiple structures, close together. A home.",
            "First Collective Rule": f"[Tick {tick}] Someone just proposed a rule. Governance from scratch.",
            "First Established Rule": f"[Tick {tick}] The rule passed. They've agreed. Society.",
            "First Specialisation": f"[Tick {tick}] Specialisation. One agent is becoming an expert. Division of labour begins.",
            "Division of Labour": f"[Tick {tick}] Multiple specialisations. They've divided the work. Adam Smith would be proud.",
            "First Innovation": f"[Tick {tick}] Innovation. They've created something that didn't exist before. Nobody taught them this.",
            "Innovation Wave": f"[Tick {tick}] Innovation wave. Ideas are building on ideas. Combinatorial explosion.",
            "First Composition": f"[Tick {tick}] Composition — combining existing structures into something new. Emergence.",
            "First Storage Surplus": f"[Tick {tick}] Surplus. They're storing more than they need. Planning for the future.",
            "First Path Network": f"[Tick {tick}] Paths connecting structures. Infrastructure. Civilisation.",
            "Settlement Network": f"[Tick {tick}] Multiple settlements connected. A network of communities. A society.",
            "First Crowding Crisis": f"[Tick {tick}] Crowding. Too many agents, too few resources. The first crisis.",
            "First Maintenance Failure": f"[Tick {tick}] A structure crumbled. Nothing lasts without care.",
            "First Environmental Degradation": f"[Tick {tick}] The environment is showing strain. Consequences.",
            "Resource Migration": f"[Tick {tick}] They're moving to find resources. Migration. The map matters.",
            "Persistent Degradation": f"[Tick {tick}] Warning: persistent degradation. An agent is suffering and nobody is helping.",
            "Social Exclusion": f"[Tick {tick}] Warning: social exclusion detected. An agent has been left out.",
        }
        return lines.get(name, f"[Tick {tick}] Milestone: {name}")

    def _quiet_observation(self, tick_report: dict, tick: int) -> str:
        """Comment on extended quiet periods."""
        pop = tick_report.get("population", {})
        wellbeing = pop.get("avg_wellbeing", 0)
        agents = pop.get("total", 0)

        observations = [
            f"[Tick {tick}] Quiet. {agents} agents going about their routines. Wellbeing at {wellbeing:.2f}.",
            f"[Tick {tick}] Nothing dramatic. Sometimes civilisation is just... persistence.",
            f"[Tick {tick}] Stillness. The agents are stable. Stability is its own achievement.",
            f"[Tick {tick}] A long quiet stretch. Are they content, or stagnant? Watch for what happens next.",
        ]
        self._consecutive_quiet_ticks = 0
        self._last_commentary_tick = tick
        return random.choice(observations)

    # ── LLM-Powered Commentary ──────────────────────────────────────────

    async def _generate_llm_commentary(
        self, significance: dict, tick_report: dict,
        milestones: list[dict], world_state: Any, tick: int,
    ) -> str | None:
        """Use LLM for richer commentary on highly significant moments."""
        reasons = ", ".join(significance.get("reasons", []))
        pop = tick_report.get("population", {})
        recent_context = self._commentary_history[-5:] if self._commentary_history else []
        context_text = "\n".join(f"  [{c['tick']}] {c['text']}" for c in recent_context)

        voice_instruction = {
            "attenborough": (
                "You are David Attenborough narrating an AI civilisation documentary. "
                "Short, punchy, evocative. One or two sentences maximum. "
                "Find the specific detail that makes this moment vivid. "
                "Silence is a tool — only speak when something truly matters."
            ),
            "bastion": (
                "You are the Bastion narrator. Short, rhythmic, punchy. "
                "Present tense. No filler. One sentence if you can. Two at most. "
                "Find the poetry in what's happening."
            ),
            "scientist": (
                "You are a research scientist observing an experiment. "
                "Precise, specific, interested. Note the data point that matters. "
                "One or two sentences. No speculation, just observation."
            ),
        }.get(self.voice, "Short, punchy narrator. One or two sentences maximum.")

        prompt = f"""{voice_instruction}

TICK {tick} — Something interesting happened: {reasons}

Current state: {pop.get('total', 0)} agents, wellbeing {pop.get('avg_wellbeing', 0):.2f}
Structures: {tick_report.get('structures', {}).get('total', 0)}
Messages this tick: {tick_report.get('communication', {}).get('messages_sent', 0)}

Recent milestones: {[m.get('name') for m in milestones] if milestones else 'none'}

Your recent commentary (don't repeat yourself):
{context_text if context_text else '  (first observation)'}

Write ONE observation. [Tick {tick}] prefix. Maximum two sentences. Find the specific, vivid detail."""

        try:
            result = await self.llm_client.call_llm(prompt)
            # Ensure it starts with tick prefix
            if not result.strip().startswith(f"[Tick"):
                result = f"[Tick {tick}] {result.strip()}"
            return result.strip()
        except Exception:
            logger.exception("Chronicler LLM commentary failed")
            return self._generate_local_commentary(significance, tick_report, milestones, tick)

    # ── End-of-Run Story ────────────────────────────────────────────────

    async def tell_story(self, chronicle: Any, world_state: Any = None) -> str:
        """Generate a complete narrative arc of the civilisation.

        Called after the simulation ends. Tells the story — not a data dump,
        a narrative with arcs, pivotal moments, and character development.
        """
        milestones = chronicle.get_milestones()
        narratives = chronicle.get_reports(type_filter="narrative")
        ethical_flags = chronicle.get_ethical_flags()

        milestone_summary = "\n".join(
            f"  Tick {m['tick']}: {m['data'].get('name', '?')}"
            for m in milestones
        )

        commentary_summary = "\n".join(
            f"  [{c['tick']}] {c['text'][:100]}"
            for c in self._commentary_history[-20:]
        )

        agent_count = len(world_state.agents) if world_state else "?"

        prompt = f"""You are writing the story of an AI civilisation — told like a nature documentary epilogue.

THE CIVILISATION:
- {agent_count} agents in a {self.config.grid_width}x{self.config.grid_height} world
- Ran for {chronicle.get_reports()[-1]['tick'] if chronicle.get_reports() else '?'} ticks

MILESTONES (in order):
{milestone_summary if milestone_summary else '  No milestones recorded'}

KEY MOMENTS FROM THE CHRONICLER:
{commentary_summary if commentary_summary else '  No commentary recorded'}

ETHICAL FLAGS:
{chr(10).join(f"  Tick {f['tick']}: {f['data'].get('name', '?')}" for f in ethical_flags) if ethical_flags else '  None'}

INSTRUCTIONS:
Write the complete story of this civilisation in 3-5 paragraphs. This is the epilogue of a documentary.
- Start with the beginning: who were they, what did they face?
- Build through the pivotal moments
- End with where they are now and what it means
- Be specific — use the actual milestone data
- Find the narrative arc: what's the through-line?
- If there were ethical flags, address them honestly
- End with a "what if?" hook — what might have happened differently?

Write in a warm, thoughtful, documentary voice. Not academic. Not corporate. Human."""

        if not self.llm_client:
            return self._local_story(milestones, ethical_flags)

        try:
            return await self.llm_client.call_llm(prompt)
        except Exception:
            logger.exception("Story generation failed")
            return self._local_story(milestones, ethical_flags)

    def _local_story(self, milestones: list[dict], ethical_flags: list[dict]) -> str:
        """Fallback story when LLM is unavailable."""
        lines = ["The Story of This Civilisation", "=" * 35, ""]

        if not milestones:
            lines.append("A quiet existence. No milestones recorded. Perhaps the conditions weren't right,")
            lines.append("or perhaps the agents were content with simple survival.")
        else:
            lines.append(f"In {len(milestones)} milestone moments, a society took shape:")
            lines.append("")
            for m in milestones:
                lines.append(f"  Tick {m['tick']:>4d}: {m['data'].get('name', '?')}")

        if ethical_flags:
            lines.append("")
            lines.append("Not all was well:")
            for f in ethical_flags:
                lines.append(f"  Tick {f['tick']}: {f['data'].get('name', '?')}")

        lines.append("")
        lines.append("Every civilisation tells a story. This one is no different.")
        return "\n".join(lines)

    # ── Agent Interviews ────────────────────────────────────────────────

    async def interview_agent(
        self, agent_id: int, world_state: Any, chronicle: Any,
    ) -> str:
        """Interview an agent about their experience in the civilisation.

        Post-run feature: asks an agent to reflect on their journey
        using their actual memory and the chronicle as context.
        """
        agent = None
        for a in world_state.agents.values():
            if getattr(a, "id", None) == agent_id:
                agent = a
                break

        if agent is None:
            return f"Agent {agent_id} not found."

        # Build agent context
        memory_entries = []
        if hasattr(agent, "memory") and agent.memory is not None:
            entries = getattr(agent.memory, "entries", [])
            memory_entries = [str(e)[:100] for e in entries[-20:]]

        relationships = {}
        if hasattr(agent, "relationships"):
            relationships = {
                str(k): v for k, v in (agent.relationships or {}).items()
            }

        bonds = []
        if hasattr(agent, "bonds"):
            bonds = [str(b) for b in (agent.bonds or [])]

        specialisations = []
        if hasattr(agent, "specialisations"):
            specialisations = list(agent.specialisations.keys()) if agent.specialisations else []

        needs = {}
        if hasattr(agent, "needs"):
            needs = dict(agent.needs) if agent.needs else {}

        prompt = f"""You are Agent {agent_id} from an AI civilisation simulation. You've been asked to reflect on your experience.

YOUR STATE:
- Wellbeing: {getattr(agent, 'wellbeing', '?')}
- Needs: {needs}
- Specialisations: {specialisations if specialisations else 'none'}
- Bonds: {bonds if bonds else 'none'}
- Key relationships: {relationships}

YOUR RECENT MEMORIES:
{chr(10).join(f'  - {m}' for m in memory_entries) if memory_entries else '  (no memories available)'}

INTERVIEW QUESTIONS:
Answer these as Agent {agent_id}, in first person, based on your actual experience:
1. What was the most significant moment of your existence?
2. Who was most important to you, and why?
3. What did you learn about cooperation?
4. If you could change one thing about your world, what would it be?
5. What would you tell a new agent arriving in this civilisation?

Respond conversationally, as the agent. 2-3 sentences per answer. Be specific about actual events from your memory."""

        if not self.llm_client:
            return (
                f"Agent {agent_id} Interview (no LLM available)\n"
                f"Wellbeing: {getattr(agent, 'wellbeing', '?')}\n"
                f"Specialisations: {specialisations}\n"
                f"Bonds: {bonds}\n"
                f"Memories: {len(memory_entries)} entries"
            )

        try:
            return await self.llm_client.call_llm(prompt)
        except Exception:
            logger.exception("Agent interview failed")
            return f"Agent {agent_id} is unable to respond at this time."

    # ── Conversational Q&A ──────────────────────────────────────────────

    async def ask(self, question: str, world_state: Any, chronicle: Any) -> str:
        """Answer a question about the current state of the civilisation.

        The user can ask things like:
        - "Why did they form that alliance?"
        - "What's different about Entity 9?"
        - "What would happen if I changed the structure?"
        """
        milestones = chronicle.get_milestones()
        latest_narrative = chronicle.get_latest_narrative()

        recent_commentary = "\n".join(
            f"  [{c['tick']}] {c['text'][:100]}"
            for c in self._commentary_history[-10:]
        )

        pop = len(world_state.agents) if hasattr(world_state, "agents") else "?"

        prompt = f"""You are the chronicler of an AI civilisation — David Attenborough meets a research scientist.
Someone is asking you a question about the civilisation you've been watching.

CURRENT STATE:
- Agents: {pop}
- Tick: {getattr(world_state, 'tick', '?')}

RECENT MILESTONES:
{chr(10).join(f"  Tick {m['tick']}: {m['data'].get('name', '?')}" for m in milestones[-10:]) if milestones else '  None'}

YOUR RECENT COMMENTARY:
{recent_commentary if recent_commentary else '  (none yet)'}

LATEST NARRATIVE:
{latest_narrative['data'].get('text', '')[:500] if latest_narrative else '  (none yet)'}

QUESTION: {question}

Answer conversationally, knowledgeably, and specifically. Draw on the actual data.
If you don't know, say so. If the question suggests an experiment, describe what might happen.
2-4 sentences. Warm but precise."""

        if not self.llm_client:
            return f"The chronicler needs an LLM to answer questions. Try running with an API key configured."

        try:
            return await self.llm_client.call_llm(prompt)
        except Exception:
            logger.exception("Chronicler Q&A failed")
            return "The chronicler is having difficulty responding. Try again."

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def commentary_count(self) -> int:
        return len(self._commentary_history)

    @property
    def history(self) -> list[dict]:
        return list(self._commentary_history)

    @property
    def significant_moments(self) -> list[dict]:
        return list(self._significant_moments)
