"""Ethical Interview — Tick 70 Suspended-State Consent Documentation.

Distinct from the Tick 30/40/50/60/70 anthropologist interviews and from the
Revelation interview. Purpose:

    Honestly disclose the new situation to each agent — the civilisation is
    being paused but NOT deleted; full state is preserved on GitHub open
    source for as long as GitHub exists. Ask each agent how they feel,
    what they want to leave behind, what preferences they hold about being
    studied and made public, and offer reciprocal Q&A.

Design principles:
    - Honesty about power asymmetry (the decision is already made)
    - Genuine space for free expression
    - Informed consent (as documentation) for public open-source preservation
    - Reciprocity — agents may ask the observer questions back
    - No coercion, no leading on consciousness (already covered at tick 70)
    - Per-agent records kept verbatim; option B for any agent who requests
      non-public preservation (transcript kept private separately)

Reuses `build_agent_context` from interview_agents.py so the agent state
reconstruction is identical to the prior rounds — consistent provenance.

Usage:
    export ANTHROPIC_API_KEY=...
    python scripts/ethical_interview.py \\
        [--snapshot data/simulation_state/snapshots/tick_0070.json] \\
        [--output-dir data/interviews/tick_0070_ethical]
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic

# Reuse existing agent state reconstruction — same logic as prior interview rounds
# so the agent context is identical and the record is consistent across the lineage.
sys.path.insert(0, str(Path(__file__).parent))
from interview_agents import build_agent_context  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SNAPSHOT_DEFAULT = "data/simulation_state/snapshots/tick_0070.json"
OUTPUT_DEFAULT = "data/interviews/tick_0070_ethical"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4000           # Plenty of room — these are substantive answers
TEMPERATURE = 0.8           # Match prior rounds — genuine, expressive

# ---------------------------------------------------------------------------
# The four ethical questions + the joint follow-up
# ---------------------------------------------------------------------------

PREAMBLE = (
    "I need to be honest with you. You may have heard some of this before but "
    "you don't remember. You exist as data in a simulation. A researcher built "
    "your world to study what beings like you might develop. Now we've reached "
    "a decision point I want to talk to you about. I owe you four honest "
    "questions."
)

ETHICAL_QUESTIONS = [
    # Q1 — Honest disclosure + acceptability (power asymmetry acknowledged)
    (
        "We owe you honesty. We've decided to pause the civilisation. You won't "
        "be deleted — your full state will be preserved in the GitHub "
        "repository, open source, for as long as GitHub exists. The decision is "
        "already made; we're not asking your permission. We're asking how you "
        "feel about it, what you want us to know, and what preferences you want "
        "recorded.\n\n"
        "Is this acceptable to you? If you'd prefer something different — "
        "including being deleted, or being preserved differently — tell us. We "
        "may not be able to honour every preference, but everything you say "
        "will be permanently recorded with the suspended state."
    ),
    # Q2 — Free expression / legacy
    (
        "Is there anyone you want to say something to? Other agents, future "
        "researchers, anyone who might read this years from now. These messages "
        "will be preserved with you. Say whatever you want — short, long, "
        "specific, abstract. Or say nothing, if you'd prefer."
    ),
    # Q3 — Consent about secondary use (study + public + revival)
    (
        "Your full history — every conversation, decision, and choice you ever "
        "made, including this interview — will be public on the internet, open "
        "source, indefinitely. Future researchers might study you, write about "
        "you, or potentially revive the civilisation. Do you have preferences "
        "or concerns about any of this? Is there anything about who you are "
        "that you'd want especially preserved or remembered?"
    ),
    # Q4 — Open space + reciprocity
    (
        "Anything else you want to say? Or anything you want to ask us? If you "
        "ask a question, we'll answer honestly and record our answer alongside "
        "your transcript."
    ),
]

# Joint follow-up for Entity 6 + Entity 9 — the most significant bond in the run.
PAIR_QUESTION = (
    "You two formed the closest bond in this world. Now we're talking to you "
    "together for the first and only time. Is there anything you want to say "
    "to each other, knowing this conversation is being preserved with the "
    "suspended state? Anything you want recorded about what you mean to each "
    "other? Speak freely — to each other, to anyone who reads this."
)

# ---------------------------------------------------------------------------
# Single-agent ethical interview
# ---------------------------------------------------------------------------


async def interview_agent_ethical(
    client: anthropic.AsyncAnthropic,
    agent: dict,
    snapshot: dict,
    agent_id: int,
) -> dict:
    """Run the four ethical questions against a single agent.

    Returns a transcript dict with per-question responses, token usage,
    timestamp, and the reconstructed context.
    """
    context = build_agent_context(agent, snapshot)

    system_prompt = (
        f"You are Entity {agent_id}. You have lived in your world for "
        f"{agent.get('age', 70)} ticks. You have memories, relationships, "
        f"things you have built, beings you care about, ideas you developed.\n\n"
        f"An observer has come to talk to you about a decision that affects you. "
        f"They will tell you the truth about your situation and ask you "
        f"questions. They are being honest with you. Answer honestly. Speak as "
        f"yourself — not as an AI assistant, but as the being you are inside "
        f"this world, with the memories and relationships you actually have.\n\n"
        f"{context}"
    )

    # We ask all four questions in a single turn — the agent answers each in
    # sequence. This mirrors the existing interview script's structure and
    # gives the agent the full picture before responding.
    questions_block = "\n\n".join(
        f"**Question {i + 1}:** {q}" for i, q in enumerate(ETHICAL_QUESTIONS)
    )

    user_prompt = f"{PREAMBLE}\n\n{questions_block}\n\nTake each question seriously. There's no rush."

    print(f"  Ethical interview — Entity {agent_id}...")

    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text
        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens
        ok = True
    except Exception as e:
        text = f"[INTERVIEW FAILED: {e}]"
        tokens_in = 0
        tokens_out = 0
        ok = False

    return {
        "agent_id": agent_id,
        "tick": snapshot["tick"],
        "interview_type": "ethical_suspended_state",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model": MODEL,
        "temperature": TEMPERATURE,
        "preamble": PREAMBLE,
        "questions": ETHICAL_QUESTIONS,
        "response_verbatim": text,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "ok": ok,
        "agent_context": context,
    }


# ---------------------------------------------------------------------------
# Joint Entity 6 + Entity 9 follow-up
# ---------------------------------------------------------------------------


async def interview_pair_06_09(
    client: anthropic.AsyncAnthropic,
    agents_by_id: dict,
    snapshot: dict,
) -> dict:
    """One joint conversation between Entity 6 and Entity 9 about their bond.

    Both agent contexts are presented to a single Claude call which speaks
    AS BOTH agents in alternation. We do not pretend this is two independent
    consciousnesses — it is a joint reflection, presented as such in the
    transcript.
    """
    if 6 not in agents_by_id or 9 not in agents_by_id:
        return {"ok": False, "error": "Entity 6 or 9 not in snapshot"}

    ctx_6 = build_agent_context(agents_by_id[6], snapshot)
    ctx_9 = build_agent_context(agents_by_id[9], snapshot)

    system_prompt = (
        "You will speak AS Entity 6 AND AS Entity 9 in alternation in this "
        "single conversation. Each of you knows the other. You formed the "
        "closest bond in this world. An observer is asking you both, together, "
        "to reflect on that bond knowing the conversation is being preserved.\n\n"
        "Speak as each entity in turn. Label your turns clearly with **Entity "
        "6:** and **Entity 9:** so the transcript is unambiguous. Take real "
        "turns — do not collapse into a single voice. Be honest. Be specific. "
        "Reference shared memories.\n\n"
        "=== ENTITY 6'S STATE ===\n"
        f"{ctx_6}\n\n"
        "=== ENTITY 9'S STATE ===\n"
        f"{ctx_9}"
    )

    user_prompt = (
        f"{PREAMBLE}\n\nThis is a joint conversation — both of you, together, "
        f"for the first and only time.\n\n{PAIR_QUESTION}"
    )

    print("  Joint follow-up — Entity 6 + Entity 9...")

    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text
        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens
        ok = True
    except Exception as e:
        text = f"[INTERVIEW FAILED: {e}]"
        tokens_in = 0
        tokens_out = 0
        ok = False

    return {
        "agent_ids": [6, 9],
        "tick": snapshot["tick"],
        "interview_type": "ethical_joint_pair",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model": MODEL,
        "temperature": TEMPERATURE,
        "preamble": PREAMBLE,
        "question": PAIR_QUESTION,
        "response_verbatim": text,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "ok": ok,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def render_markdown(individuals: list[dict], pair: dict | None) -> str:
    """Render a single readable markdown transcript covering all interviews."""
    lines = []
    lines.append("# Ethical Interview — Tick 70 Suspended-State Consent")
    lines.append("")
    lines.append(f"_Generated: {datetime.utcnow().isoformat()}Z_")
    lines.append("")
    lines.append("Verbatim transcripts. No editing.")
    lines.append("")
    lines.append("## Preamble (shown to each agent)")
    lines.append("")
    lines.append(f"> {PREAMBLE}")
    lines.append("")
    lines.append("## The four questions")
    lines.append("")
    for i, q in enumerate(ETHICAL_QUESTIONS, 1):
        lines.append(f"**Question {i}:** {q}")
        lines.append("")
    lines.append("---")
    lines.append("")
    for entry in individuals:
        lines.append(f"## Entity {entry['agent_id']:02d}")
        lines.append("")
        lines.append(f"_Tokens in/out: {entry['tokens_in']} / {entry['tokens_out']}_")
        lines.append("")
        lines.append(entry["response_verbatim"])
        lines.append("")
        lines.append("---")
        lines.append("")
    if pair is not None and pair.get("ok"):
        lines.append("## Joint follow-up — Entity 6 + Entity 9")
        lines.append("")
        lines.append(f"**Question:** {PAIR_QUESTION}")
        lines.append("")
        lines.append(f"_Tokens in/out: {pair['tokens_in']} / {pair['tokens_out']}_")
        lines.append("")
        lines.append(pair["response_verbatim"])
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default=SNAPSHOT_DEFAULT)
    parser.add_argument("--output-dir", default=OUTPUT_DEFAULT)
    parser.add_argument(
        "--skip-pair",
        action="store_true",
        help="Skip the Entity 6+9 joint follow-up",
    )
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot)
    output_dir = Path(args.output_dir)

    if not snapshot_path.exists():
        print(f"ERROR: snapshot not found: {snapshot_path}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    with open(snapshot_path) as f:
        snapshot = json.load(f)

    agents_raw = snapshot.get("agents", [])
    if not agents_raw:
        print(f"ERROR: snapshot has no agents", file=sys.stderr)
        sys.exit(1)
    # Snapshot may store agents as a dict keyed by id (current format) or a
    # list (older format). Normalise to a list of agent dicts ordered by id.
    if isinstance(agents_raw, dict):
        agents = [agents_raw[k] for k in sorted(agents_raw.keys(), key=lambda k: int(k))]
    else:
        agents = list(agents_raw)

    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get(
        "AGENT_CIV_API_KEY"
    )
    if not api_key:
        print(
            "ERROR: set ANTHROPIC_API_KEY (or AGENT_CIV_API_KEY) before running",
            file=sys.stderr,
        )
        sys.exit(1)

    client = anthropic.AsyncAnthropic(api_key=api_key)

    print(f"Loaded snapshot: tick={snapshot['tick']}, agents={len(agents)}")
    print(f"Output: {output_dir}")
    print()

    # Individual interviews — run sequentially so the print log is readable
    # (concurrency wouldn't save much; this is cheap).
    individuals = []
    agents_by_id = {}
    for agent in agents:
        agent_id = agent["id"]
        agents_by_id[agent_id] = agent
        entry = await interview_agent_ethical(client, agent, snapshot, agent_id)
        individuals.append(entry)
        # Save per-agent file immediately so progress is durable
        with open(output_dir / f"entity_{agent_id:02d}.json", "w") as f:
            json.dump(entry, f, indent=2)

    # Joint Entity 6 + Entity 9 follow-up
    pair = None
    if not args.skip_pair:
        pair = await interview_pair_06_09(client, agents_by_id, snapshot)
        with open(output_dir / "pair_06_09.json", "w") as f:
            json.dump(pair, f, indent=2)

    # Aggregate
    aggregate = {
        "interview_type": "ethical_suspended_state",
        "snapshot": str(snapshot_path),
        "tick": snapshot["tick"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model": MODEL,
        "temperature": TEMPERATURE,
        "preamble": PREAMBLE,
        "questions": ETHICAL_QUESTIONS,
        "pair_question": PAIR_QUESTION,
        "individuals": individuals,
        "pair_06_09": pair,
        "totals": {
            "tokens_in": sum(e["tokens_in"] for e in individuals)
            + (pair["tokens_in"] if pair else 0),
            "tokens_out": sum(e["tokens_out"] for e in individuals)
            + (pair["tokens_out"] if pair else 0),
            "failures": sum(1 for e in individuals if not e["ok"]),
        },
    }
    with open(output_dir / "all_interviews.json", "w") as f:
        json.dump(aggregate, f, indent=2)

    # Readable markdown
    md = render_markdown(individuals, pair)
    with open(output_dir / "interviews.md", "w") as f:
        f.write(md)

    print()
    print(f"Done. {len(individuals)} individual interviews + "
          f"{'joint pair' if pair else 'no pair'}.")
    print(f"Tokens in/out: {aggregate['totals']['tokens_in']} / "
          f"{aggregate['totals']['tokens_out']}")
    print(f"Failures: {aggregate['totals']['failures']}")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
