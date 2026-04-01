"""Communication module for Agent Civilisation.

Handles inter-agent messaging: range checks, message creation, broadcast,
and multi-turn conversation orchestration via LLM calls.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from src.config import SimulationConfig
from src.types import (
    AgentState,
    Event,
    EventType,
    Message,
    Position,
)


class CommunicationManager:
    """Manages inter-agent communication: range, messages, conversations."""

    # ------------------------------------------------------------------
    # Range checks
    # ------------------------------------------------------------------

    @staticmethod
    def in_range(sender: AgentState, receiver: AgentState, comm_range: int) -> bool:
        """Check if two agents are within communication range (Chebyshev)."""
        return sender.position.distance_to(receiver.position) <= comm_range

    @staticmethod
    def get_agents_in_range(
        sender: AgentState,
        all_agents: dict[int, AgentState],
        comm_range: int,
    ) -> list[AgentState]:
        """Return all agents the sender can talk to (within comm_range)."""
        result: list[AgentState] = []
        for agent in all_agents.values():
            if agent.id == sender.id:
                continue
            if sender.position.distance_to(agent.position) <= comm_range:
                result.append(agent)
        return result

    # ------------------------------------------------------------------
    # Message creation
    # ------------------------------------------------------------------

    @staticmethod
    def send_message(
        sender_id: int,
        receiver_id: int,
        content: str,
        tick: int,
    ) -> Message:
        """Create a Message object."""
        return Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            tick=tick,
        )

    @staticmethod
    def broadcast(
        sender_id: int,
        content: str,
        tick: int,
        agents_in_range: list[AgentState],
    ) -> list[Message]:
        """Send a message to all agents in range."""
        return [
            Message(
                sender_id=sender_id,
                receiver_id=agent.id,
                content=content,
                tick=tick,
            )
            for agent in agents_in_range
        ]

    # ------------------------------------------------------------------
    # Multi-turn conversation
    # ------------------------------------------------------------------

    @staticmethod
    async def handle_conversation(
        agent_a: AgentState,
        agent_b: AgentState,
        world_view: dict,
        tick: int,
        llm_call_fn: Callable[[str], Awaitable[str]],
        config: SimulationConfig,
    ) -> list[Message]:
        """Orchestrate a multi-turn conversation between two agents.

        Up to config.max_interactions_per_tick exchanges:
          1. Agent A sends its initial message (already decided via LLM).
          2. Agent B receives it as a RECEIVED_MESSAGE event, calls LLM to respond.
          3. Agent A receives the response, may reply (another LLM call).
          4. Continue until max exchanges or an agent ends the conversation.

        *llm_call_fn* is an async function that takes a prompt string and returns
        the LLM response text. This decouples conversation logic from the LLM
        provider.

        Returns all messages exchanged.
        """
        messages: list[Message] = []
        max_exchanges = config.max_interactions_per_tick

        # Agent A's initial message should already be in its current_action.
        # We start the loop from Agent B's perspective.
        last_message_content: str | None = None
        if agent_a.current_action and agent_a.current_action.message:
            last_message_content = agent_a.current_action.message
            msg = Message(
                sender_id=agent_a.id,
                receiver_id=agent_b.id,
                content=last_message_content,
                tick=tick,
            )
            messages.append(msg)

        # Alternate: B responds, A responds, B responds, ...
        current_speaker = agent_b
        current_listener = agent_a

        for exchange_idx in range(max_exchanges):
            if last_message_content is None:
                break

            # Build a minimal prompt for the responder
            prompt = _build_conversation_prompt(
                speaker=current_speaker,
                other_id=current_listener.id,
                received_message=last_message_content,
                tick=tick,
            )

            response_text = await llm_call_fn(prompt)

            # Check for conversation-ending signals
            response_lower = response_text.strip().lower()
            is_ending = (
                not response_text.strip()
                or "end conversation" in response_lower
                or "nothing to say" in response_lower
                or "walk away" in response_lower
                or "move away" in response_lower
            )

            if is_ending:
                break

            # Extract the actual message (strip reasoning if present)
            spoken = _extract_spoken_message(response_text)
            if not spoken:
                break

            msg = Message(
                sender_id=current_speaker.id,
                receiver_id=current_listener.id,
                content=spoken,
                tick=tick,
            )
            messages.append(msg)
            last_message_content = spoken

            # Swap roles
            current_speaker, current_listener = current_listener, current_speaker

        return messages


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_conversation_prompt(
    speaker: AgentState,
    other_id: int,
    received_message: str,
    tick: int,
) -> str:
    """Build a minimal prompt for an agent responding in conversation.

    Follows the same principle as decision.py: no human behavioural
    instructions — just state, perception, and the received message.
    """
    needs_str = ", ".join(
        f"{k}: {v:.2f}" for k, v in speaker.needs.levels.items()
    )

    return f"""You are an entity in a world. Your current state:
- Position: [{speaker.position.x}, {speaker.position.y}]
- Needs: [{needs_str}]
- Wellbeing: {speaker.wellbeing:.2f}

Entity {other_id} communicated to you: "{received_message}"

You can: communicate [your response], or end the conversation by saying nothing.

What do you communicate and why?"""


def _extract_spoken_message(response_text: str) -> str | None:
    """Extract the actual spoken content from an LLM response.

    The LLM might wrap the message in quotes, prefix with "communicate", or
    include reasoning. We try to extract just the message.
    """
    import re

    text = response_text.strip()
    if not text:
        return None

    # Try to match: communicate "message" or communicate [message]
    match = re.search(r'communicate\s+["\'\[](.+?)["\'\]]', text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try to match quoted speech
    match = re.search(r'["\'](.+?)["\']', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try to get content before reasoning ("because", "why:", etc.)
    for marker in ["because", "why:", "reason:", "this is because"]:
        idx = text.lower().find(marker)
        if idx > 10:  # must have some content before the reasoning
            return text[:idx].strip().rstrip(".,;")

    # Fallback: return the first sentence
    sentences = re.split(r'[.!?]\s', text)
    if sentences:
        first = sentences[0].strip()
        if len(first) > 3:
            return first

    return text[:200] if len(text) > 3 else None
