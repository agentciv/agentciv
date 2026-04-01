"""Agent runtime package for Agent Civilisation.

Public API:
  Agent              -- high-level agent wrapper (agent.py)
  MemoryStore        -- memory management with eviction (memory.py)
  CommunicationManager -- inter-agent messaging (communication.py)
  LLMClient          -- provider-agnostic async LLM wrapper (llm.py)

  Perception functions (perception.py):
    visible_tiles, visible_resources, visible_agents, detect_events,
    observe_after_action

  Decision functions (decision.py):
    deterministic_action, build_prompt, build_world_view, parse_response
"""

from src.agents.agent import Agent
from src.agents.memory import MemoryStore
from src.agents.perception import (
    detect_events,
    observe_after_action,
    visible_agents,
    visible_resources,
    visible_tiles,
)
from src.agents.decision import (
    build_prompt,
    build_world_view,
    deterministic_action,
    parse_response,
)
from src.agents.communication import CommunicationManager
from src.agents.llm import LLMClient

# Graceful import of AgenticLoop — it's being built by another agent
# and may not exist yet.
try:
    from src.agents.agentic_loop import AgenticLoop
    _AGENTIC_LOOP_AVAILABLE = True
except ImportError:
    AgenticLoop = None  # type: ignore[misc, assignment]
    _AGENTIC_LOOP_AVAILABLE = False

__all__ = [
    "Agent",
    "MemoryStore",
    "CommunicationManager",
    "LLMClient",
    "visible_tiles",
    "visible_resources",
    "visible_agents",
    "detect_events",
    "observe_after_action",
    "deterministic_action",
    "build_prompt",
    "build_world_view",
    "parse_response",
]

# Only export AgenticLoop if it's available
if _AGENTIC_LOOP_AVAILABLE:
    __all__.append("AgenticLoop")
