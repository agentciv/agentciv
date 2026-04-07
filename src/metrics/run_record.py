"""Structured run record for simulation output.

Provides a machine-readable summary of a simulation run,
enabling Creator Mode and other tools to analyse results
without parsing narrative text.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .emergence import EmergenceScore


@dataclass
class SimulationRunRecord:
    """Complete structured output from a simulation run."""

    # Run metadata
    run_id: str = ""
    timestamp: str = ""
    wall_time_seconds: float = 0.0

    # Configuration
    config_snapshot: dict[str, Any] = field(default_factory=dict)
    preset: str = ""  # named preset used, if any
    ticks_completed: int = 0

    # Token usage
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

    # Emergence metrics
    emergence: EmergenceScore = field(default_factory=EmergenceScore)

    # Highlights from the chronicle
    milestones: list[str] = field(default_factory=list)
    chronicle_highlights: list[str] = field(default_factory=list)

    # Per-agent summary
    agent_summary: list[dict[str, Any]] = field(default_factory=list)

    # Success indicator
    success: bool = True
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a dictionary suitable for JSON export."""
        d = {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "wall_time_seconds": round(self.wall_time_seconds, 2),
            "config_snapshot": self.config_snapshot,
            "preset": self.preset,
            "ticks_completed": self.ticks_completed,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
            "emergence": self.emergence.to_dict(),
            "milestones": self.milestones,
            "chronicle_highlights": self.chronicle_highlights,
            "agent_summary": self.agent_summary,
            "success": self.success,
            "error": self.error,
        }
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialise to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str | Path) -> Path:
        """Write the run record to a JSON file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_json())
        return p

    @classmethod
    def from_json(cls, path: str | Path) -> SimulationRunRecord:
        """Load a run record from a JSON file."""
        data = json.loads(Path(path).read_text())
        emergence_data = data.pop("emergence", {})
        emergence = EmergenceScore(**{
            k: v for k, v in emergence_data.items()
            if k in EmergenceScore.__dataclass_fields__
        })
        record = cls(emergence=emergence, **{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__ and k != "emergence"
        })
        return record


def build_agent_summary(agents: dict) -> list[dict[str, Any]]:
    """Build per-agent summary from world state agents."""
    summaries = []
    for agent_id, agent in sorted(agents.items()):
        summaries.append({
            "id": agent.id,
            "maslow_level": agent.maslow_level,
            "wellbeing": round(agent.wellbeing, 3),
            "curiosity": round(agent.curiosity, 3),
            "age": agent.age,
            "specialisations": agent.specialisations,
            "relationship_count": len(agent.relationships),
            "bonded_count": sum(1 for r in agent.relationships.values() if r.is_bonded),
            "innovations_proposed": agent.innovations_proposed,
            "goals": agent.goals[:3],  # first 3 goals
            "structures_built": agent.structures_built_count,
        })
    return summaries
