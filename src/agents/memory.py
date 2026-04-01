"""Memory store for Agent Civilisation.

Wraps an agent's memory list with eviction, summarisation, and event recording.
Eviction policy: when at capacity, drop the entry with lowest composite score
(importance * 0.7 + recency * 0.3), so old low-importance memories go first.
"""

from __future__ import annotations

from src.types import (
    Event,
    EventType,
    MemoryEntry,
)


# Importance scores for different event types — tuned to keep critical events
# and let routine ones fade.
_EVENT_IMPORTANCE: dict[EventType, float] = {
    EventType.NEEDS_CRITICAL: 0.9,
    EventType.RESOURCE_DEPLETED: 0.7,
    EventType.RESOURCE_DISCOVERED: 0.6,
    EventType.AGENT_ENTERED_PERCEPTION: 0.5,
    EventType.AGENT_LEFT_PERCEPTION: 0.3,
    EventType.WELLBEING_INCREASED: 0.6,
    EventType.ENVIRONMENTAL_CHANGE: 0.8,
    EventType.REFLECTION: 0.5,
    EventType.RECEIVED_MESSAGE: 0.7,
    EventType.PLAN_STEP_DUE: 0.4,
    EventType.STRUCTURE_DISCOVERED: 0.7,
    EventType.COMPOSITION_ATTEMPTED: 0.8,
    EventType.INNOVATION_PROPOSED: 0.9,
    EventType.RULE_PROPOSED: 0.8,
    EventType.SPECIALISATION_GAINED: 0.8,
}


class MemoryStore:
    """Manages an agent's memory list with capacity-aware eviction."""

    def __init__(self, memories: list[MemoryEntry], capacity: int) -> None:
        self.memories = memories
        self.capacity = capacity

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def add(self, entry: MemoryEntry) -> None:
        """Append a memory entry, evicting the least valuable if at capacity."""
        if len(self.memories) >= self.capacity:
            self._evict()
        self.memories.append(entry)

    def get_all(self) -> list[MemoryEntry]:
        """Return the full memory list (mutable reference)."""
        return self.memories

    def get_summary(
        self,
        max_entries: int = 20,
        context_hints: list[str] | None = None,
    ) -> str:
        """Return the most important/recent memories as a text block for LLM prompts.

        Entries are sorted by a composite score (importance * 0.7 + recency * 0.3)
        with an optional context relevance boost (+0.2 if the memory text contains
        any of the context_hints keywords). This makes agents recall memories about
        nearby agents, current location, or current activity more readily.
        """
        if not self.memories:
            return "No memories yet."

        scored = self._score_all()

        # Boost relevance for contextually matching memories
        if context_hints:
            hints_lower = [h.lower() for h in context_hints]
            boosted: list[tuple[MemoryEntry, float]] = []
            for entry, score in scored:
                summary_lower = entry.summary.lower()
                if any(hint in summary_lower for hint in hints_lower):
                    boosted.append((entry, score + 0.2))
                else:
                    boosted.append((entry, score))
            scored = boosted

        # Sort descending by composite score, take the top entries
        scored.sort(key=lambda pair: pair[1], reverse=True)
        top = scored[:max_entries]

        # Re-sort by tick descending so the output reads newest-first
        top.sort(key=lambda pair: pair[0].tick, reverse=True)

        lines: list[str] = []
        for entry, _ in top:
            entry.access_count += 1
            lines.append(f"Tick {entry.tick}: {entry.summary}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Recording helpers
    # ------------------------------------------------------------------

    def record_event(self, event: Event) -> MemoryEntry:
        """Convert an Event into a MemoryEntry and store it."""
        importance = _EVENT_IMPORTANCE.get(event.type, 0.5)
        summary = self._event_to_summary(event)
        entry = MemoryEntry(tick=event.tick, summary=summary, importance=importance)
        self.add(entry)
        return entry

    def record_interaction(self, agent_id: int, message: str, tick: int) -> MemoryEntry:
        """Record a communication event as a memory."""
        entry = MemoryEntry(
            tick=tick,
            summary=f"Communicated with Agent {agent_id}: {message}",
            importance=0.6,
        )
        self.add(entry)
        return entry

    def record_goal_change(self, goal: str, tick: int, is_new: bool = True) -> MemoryEntry:
        """Record when the agent sets or completes a goal."""
        if is_new:
            summary = f"Set new goal: {goal}"
            importance = 0.7
        else:
            summary = f"Completed goal: {goal}"
            importance = 0.8  # completions are more memorable
        entry = MemoryEntry(tick=tick, summary=summary, importance=importance)
        self.add(entry)
        return entry

    def record_plan_change(self, plan: list[str], tick: int) -> MemoryEntry:
        """Record when the agent updates its plan."""
        if plan:
            steps_preview = " -> ".join(plan[:3])
            if len(plan) > 3:
                steps_preview += f" ... ({len(plan)} steps total)"
            summary = f"Updated plan: {steps_preview}"
        else:
            summary = "Cleared plan (no steps)."
        entry = MemoryEntry(tick=tick, summary=summary, importance=0.6)
        self.add(entry)
        return entry

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_all(self) -> list[tuple[MemoryEntry, float]]:
        """Compute composite scores for all memories.

        recency = 1.0 for the newest entry, 0.0 for the oldest.
        composite = importance * 0.7 + recency * 0.3
        """
        n = len(self.memories)
        if n <= 1:
            return [(m, m.importance) for m in self.memories]

        scored: list[tuple[MemoryEntry, float]] = []
        for idx, entry in enumerate(self.memories):
            recency = idx / (n - 1)  # 0.0 for oldest (index 0), 1.0 for newest
            composite = entry.importance * 0.7 + recency * 0.3
            scored.append((entry, composite))
        return scored

    def _evict(self) -> None:
        """Remove the single entry with the lowest composite score."""
        if not self.memories:
            return
        scored = self._score_all()
        worst_entry, _ = min(scored, key=lambda pair: pair[1])
        self.memories.remove(worst_entry)

    @staticmethod
    def _event_to_summary(event: Event) -> str:
        """Produce a human-readable one-liner from an Event."""
        data = event.data
        match event.type:
            case EventType.AGENT_ENTERED_PERCEPTION:
                other = data.get("other_agent_id", "unknown")
                return f"Agent {other} entered perception range."
            case EventType.AGENT_LEFT_PERCEPTION:
                other = data.get("other_agent_id", "unknown")
                return f"Agent {other} left perception range."
            case EventType.RESOURCE_DEPLETED:
                pos = data.get("position", "?")
                rtype = data.get("resource_type", "?")
                return f"Resource {rtype} depleted at {pos}."
            case EventType.RESOURCE_DISCOVERED:
                pos = data.get("position", "?")
                rtype = data.get("resource_type", "?")
                return f"Discovered {rtype} resource at {pos}."
            case EventType.NEEDS_CRITICAL:
                need = data.get("need_type", "unknown")
                level = data.get("level", "?")
                return f"Need '{need}' reached critical level ({level})."
            case EventType.WELLBEING_INCREASED:
                amount = data.get("amount", "?")
                return f"Wellbeing increased by {amount}."
            case EventType.ENVIRONMENTAL_CHANGE:
                desc = data.get("description", "unknown change")
                return f"Environmental change detected: {desc}."
            case EventType.REFLECTION:
                return "Periodic self-reflection moment."
            case EventType.RECEIVED_MESSAGE:
                sender = data.get("sender_id", "unknown")
                msg = data.get("content", "") or data.get("message", "")
                return f"Received message from Agent {sender}: {msg}"
            case EventType.PLAN_STEP_DUE:
                step = data.get("next_step", "unknown")
                remaining = data.get("remaining", "?")
                return f"Plan step due: {step} ({remaining} steps remaining)."
            case EventType.STRUCTURE_DISCOVERED:
                stype = data.get("structure_type", "unknown")
                pos = data.get("position", "?")
                return f"Discovered {stype} structure at {pos}."
            case EventType.COMPOSITION_ATTEMPTED:
                inputs = data.get("inputs", [])
                result = data.get("result", "unknown")
                return f"Attempted composition: {' + '.join(inputs)} -> {result}."
            case EventType.INNOVATION_PROPOSED:
                desc = data.get("description", "unknown")
                success = data.get("success", False)
                return f"Proposed innovation: {desc} ({'accepted' if success else 'rejected'})."
            case EventType.RULE_PROPOSED:
                text = data.get("text", "unknown")
                return f"Proposed collective rule: {text}."
            case EventType.SPECIALISATION_GAINED:
                activity = data.get("activity", "unknown")
                return f"Gained specialisation in {activity}."
            case _:
                return event.summary()
