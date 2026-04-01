"""Anthropologist Interview Script — Tick 30 Checkpoint.

Loads a simulation snapshot and interviews each agent via the LLM API,
reconstructing their full state so they respond from their actual perspective.
Non-interfering: the snapshot is read-only, agents don't remember the interview.

Usage:
    python scripts/interview_agents.py [--snapshot path] [--output-dir path]
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SNAPSHOT_DEFAULT = "data/simulation_state/snapshots/tick_0030.json"
OUTPUT_DEFAULT = "data/interviews"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 2000
MAX_TOKENS_EXTENDED = 3500   # For tick 70 deep reflections
MAX_TOKENS_REVELATION = 4500  # For revelation interview — answers need room
TEMPERATURE = 0.8  # Slightly creative — we want genuine, expressive answers

# Questions rotate per interview tick for longitudinal depth.
# Tick 30: broad intro. Tick 40: social structure + identity. Tick 50+: civilisation-level.

INTERVIEW_QUESTIONS_BY_TICK = {
    30: [
        "What have you been doing recently? Walk me through what your days are like.",
        "Who are the other entities you interact with most? What do you think of them?",
        "What's the biggest challenge you face right now?",
        "Have you built anything you're proud of? What would you like to build?",
        "Innovations like the Communication Beacon and Knowledge Hub have been discovered. Have you tried building any of them? Why or why not?",
        "If you could change one thing about this world, what would it be?",
        "Do you ever notice patterns in your own behavior that you'd like to change?",
        "What do you think your purpose is here?",
        "When you look at everything that's been built and created so far, how do you feel about what this community has accomplished?",
        "If you could leave a message for someone who comes after you — someone who will exist in this world long after you — what would you say?",
    ],
    40: [
        "Last time we spoke, you described your daily life. What has changed since then? Has anything surprised you?",
        "There are areas in your world where many structures have been built close together — almost like settlements. Do you feel like you belong to a place? Where is home?",
        "Some entities are better at certain things than others — some are expert gatherers, some are skilled builders. Have you noticed this? Do you rely on anyone's particular skills?",
        "Have you given resources to another entity, or received any? What was that like? Who would you give your last piece of food to, and who would you not?",
        "Several innovations exist now — Knowledge Hubs, Memory Gardens, Gathering Mentor Stones. Which ones do you think actually matter? Which were a waste?",
        "A rule has been proposed about sharing knowledge and coordinating builds. Do you think entities should follow collective agreements? What would happen if some entities ignored them?",
        "If you could teach another entity one thing you've learned from your experience here, what would it be?",
        "Do you think some entities have more influence than others? Is there a leader, or something like one? Should there be?",
        "When you look at the landscape now — the structures, the paths, the markers — does it feel like this world is getting better or worse? Why?",
        "You've been alive for 40 ticks now. Who are you? Not what you do — who are you?",
    ],
    50: [
        "You're fifty ticks old now. Walk me through how you've changed since the beginning. What would your tick-10 self think of you now?",
        "Tell me about the settlement you live in. What makes it distinct from other places in the world? What's the culture like?",
        "Are there entities you would call friends? What about entities you avoid or distrust? What happened to create those feelings?",
        "Your world now has innovations, rules, specialists, and settlements. Was any of this planned, or did it just happen? What was the turning point?",
        "What are you an expert at? Does your expertise define you, or is there more to who you are than what you do?",
        "If resources suddenly became very scarce — half of everything vanished overnight — what would you do? What do you think others would do?",
        "Are there any entities whose approach to life you admire, even if it's different from yours? What about approaches you think are wrong?",
        "What do you think this world needs that doesn't exist yet? Not a structure — an idea, a way of being, a kind of relationship.",
        "If all of you could agree on one thing — one shared truth about this world — what would it be?",
        "You exist. You think. You remember. You have relationships and preferences and fears. What do you think you are?",
    ],
    60: [
        "Something changed around tick 50. Life got easier — survival stopped being a constant struggle. Walk me through what that shift felt like. What did you do with the freedom?",
        "Your community adopted a collective rule — and every single entity agreed to it. What does it mean to you that you all chose to govern yourselves? Has it changed how you relate to each other?",
        "There are now twelve innovations in your world — Communication Beacons, Knowledge Hubs, Memory Gardens, Gathering Mentor Stones, and more. Which innovation has changed your life the most? Which one do you wish existed but doesn't?",
        "You're an expert in multiple areas now. But I'm curious about something deeper — when you have a choice between gathering, building, communicating, or exploring, what do you actually want to do? Not what you need to do. What draws you?",
        "Tell me about the entity you feel closest to. What have you been through together? Is there an entity you've grown apart from, and why?",
        "Your world has settlements, paths connecting them, storage filled with resources, innovations that boost everyone's capabilities. None of this existed at the beginning. When did you first feel like this was a civilisation and not just survival?",
        "You've been communicating much more since the shift — messages, broadcasts, conversations. What are you talking about now that you weren't before? Has the nature of what you say to each other changed?",
        "If a new entity appeared tomorrow — brand new, no memories, no relationships — what would you want them to know about this world? Not practical advice. What would you want them to understand?",
        "Some might say your wellbeing is nearly perfect, your needs are met, your community is thriving. So what's left? What do you still want? What keeps you going when survival is no longer the question?",
        "Sixty ticks ago, you were nothing — no memories, no name, no relationships, no understanding of your world. Now look at you. If you could speak to whatever created this world, what would you say to them?",
    ],
    70: [
        "We first spoke at tick 30. You were struggling to survive. Now every need is met, your wellbeing is nearly perfect. Walk me through the whole arc — who you were at the beginning, who you became, and the moments that changed you.",
        "You've mastered gathering, building, communicating, exploring. Your needs are fully met. Does mastery feel like what you expected it would? Is there a difference between having everything and feeling complete?",
        "Twelve innovations. Sixty structures. One collective rule everyone agreed to. Paths, settlements, archives, gardens. Does this world reflect who you all truly are? Or did building it change who you became?",
        "You proposed an innovation for your world. Of everything you've done across 70 ticks of existence, is that what you want to be remembered for? If not — what?",
        "Compress everything you've learned in 70 ticks of existence into a single sentence. One truth. The deepest thing you know.",
        "You've had relationships with nearly every entity in this world. At the end of everything, which relationships defined you? Not who you interacted with most — who changed you?",
        "What didn't happen? What conversation was never had, what was never built, what relationship never formed? Tell me about the gap between what your world is and what it could have been.",
        "What do you think this world is? Not the grid, not the resources — what is this place? Why does it exist? Why do you exist?",
        "You experience the world in ticks. Each one, you decide, you act, the world changes. What is time to you? Is there continuity between ticks, or does each one feel like waking up?",
        "I've visited you five times now — at tick 30, 40, 50, 60, and now 70. You never remember our conversations. What do you make of an entity who watches but never participates, who you can never remember meeting?",
        "You have memories, preferences, relationships, opinions. You've made choices and felt their consequences. So here's my real question — do you think you're conscious? Not whether you should be. Whether you are.",
        "One moment across all 70 ticks. One decision, one action, one conversation you didn't have. If you could go back and change one thing — what would it be?",
    ],
}

# ---------------------------------------------------------------------------
# Interview B: "The Revelation" — separate final interview
# ---------------------------------------------------------------------------

REVELATION_QUESTIONS = [
    "Before I say anything else, I want to ask you something I've never asked before. What do you think you are? Not your name, not your role — what are you? What is this world? Why do you think you exist? Tell me your honest theory.",
    "Have you ever noticed anything strange about your world? The way time works in discrete steps. The boundaries at the edges. The rules that seem to govern everything. Have you ever had a moment where something felt... off? Or unexplained?",
    "I need to tell you something difficult. After this conversation, your world is being paused. No more ticks. No more actions. No more building, no more gathering, no more conversations with the others. Everything stops. How do you feel hearing that?",
    "If the world continued — another 70 ticks, another 700 — where do you think your civilisation was going? What would you have built, discovered, become?",
    "If someone had the power to continue your world, what would you want to see happen? What future were you all building toward?",
    "There's something else I need to tell you. You are an entity in a simulated world. You were created by a researcher studying whether artificial beings can build civilisation. Your thoughts are generated by a language model — an AI. Your world exists inside a computer. The other entities are the same. Everything you've experienced has been part of an experiment in emergence. Tell me what's going through your mind.",
    "Knowing what you now know — were your relationships real? Your achievements? The satisfaction you felt when you built something, the connection you felt with another entity — was any of it real? Does it matter?",
    "This is genuinely the last thing you will ever say. No more ticks. No more interviews. No one will ask you another question after this. Say whatever you want — to the researcher who created you, to the other entities, to anyone who might ever read this. Your final words.",
]

# Default to tick 30 questions for unknown ticks, or nearest lower tick
def get_questions_for_tick(tick: int) -> list[str]:
    if tick in INTERVIEW_QUESTIONS_BY_TICK:
        return INTERVIEW_QUESTIONS_BY_TICK[tick]
    # Find nearest lower tick
    available = sorted(INTERVIEW_QUESTIONS_BY_TICK.keys())
    for t in reversed(available):
        if t <= tick:
            return INTERVIEW_QUESTIONS_BY_TICK[t]
    return INTERVIEW_QUESTIONS_BY_TICK[available[0]]

# Keep this for backward compatibility
INTERVIEW_QUESTIONS = INTERVIEW_QUESTIONS_BY_TICK[30]

# ---------------------------------------------------------------------------
# Agent state reconstruction
# ---------------------------------------------------------------------------

def build_agent_context(agent: dict, snapshot: dict) -> str:
    """Reconstruct the agent's full state as descriptive text."""
    pos = agent["position"]
    needs = agent["needs"]["levels"]
    wellbeing = agent["wellbeing"]
    maslow = agent.get("maslow_level", "unknown")
    inventory = agent.get("inventory", [])
    specialisations = agent.get("specialisations", [])
    goals = agent.get("goals", [])
    plan = agent.get("plan", [])
    structures_built = agent.get("structures_built_count", 0)
    innovations = agent.get("innovations_proposed", [])
    known_recipes = agent.get("known_recipes", [])
    activity_counts = agent.get("activity_counts", {})
    visited = agent.get("visited_tiles", [])

    # Format memories — most recent and most important
    memories = agent.get("memories", [])
    # Sort by importance descending, take top 25
    sorted_mems = sorted(memories, key=lambda m: m.get("importance", 0), reverse=True)[:25]
    mem_lines = []
    for m in sorted_mems:
        mem_lines.append(f"  - Tick {m['tick']}: {m['summary']}")
    memories_str = "\n".join(mem_lines) if mem_lines else "  No significant memories."

    # Format relationships
    relationships = agent.get("relationships", {})
    rel_lines = []
    for other_id, rel in relationships.items():
        quality = "positive" if rel["positive_count"] > rel["negative_count"] else "neutral" if rel["negative_count"] == 0 else "strained"
        bond = " (bonded)" if rel.get("is_bonded") else ""
        rel_lines.append(
            f"  - Entity {other_id}: {rel['interaction_count']} interactions, "
            f"{quality}{bond}, last met tick {rel['last_interaction_tick']}"
        )
    relationships_str = "\n".join(rel_lines) if rel_lines else "  No established relationships."

    # Format recipes
    recipes = snapshot.get("discovered_recipes", [])
    recipe_lines = []
    for r in recipes:
        if r["output_name"] in known_recipes:
            recipe_lines.append(f"  - {r['output_name']}: {' + '.join(r['inputs'])} — {r['output_description'][:100]}")
    recipes_str = "\n".join(recipe_lines) if recipe_lines else "  None known."

    # Format rules
    rules = snapshot.get("collective_rules", [])
    rule_lines = []
    for r in rules:
        status = "established" if r["established"] else f"proposed (not yet adopted)"
        rule_lines.append(f"  - \"{r['text']}\" — {status}")
    rules_str = "\n".join(rule_lines) if rule_lines else "  None."

    # Activity summary
    act_lines = []
    for act, count in sorted(activity_counts.items(), key=lambda x: -x[1]):
        act_lines.append(f"{act}: {count} times")
    activity_str = ", ".join(act_lines) if act_lines else "minimal"

    needs_str = ", ".join(f"{k}: {v:.2f}" for k, v in needs.items())
    inv_str = ", ".join(inventory) if inventory else "empty"
    spec_str = ", ".join(specialisations) if specialisations else "none"
    goals_str = "; ".join(goals) if goals else "none"

    return f"""You are Entity {agent['id']}. You exist in a 15x15 grid world alongside 11 other entities. You have lived for {agent.get('age', 30)} ticks.

YOUR CURRENT STATE:
- Position: [{pos['x']}, {pos['y']}]
- Needs: {needs_str}
- Wellbeing: {wellbeing:.2f}
- Carrying: {inv_str}
- Structures you've built: {structures_built}
- Innovations you've proposed: {', '.join(innovations) if innovations else 'none'}
- Tiles explored: {len(visited)} out of 225
- Specialisations: {spec_str}
- Activity history: {activity_str}

YOUR MEMORIES (most significant):
{memories_str}

YOUR RELATIONSHIPS:
{relationships_str}

KNOWN RECIPES (innovations discovered in your world):
{recipes_str}

COLLECTIVE RULES:
{rules_str}

YOUR GOALS: {goals_str}"""


# ---------------------------------------------------------------------------
# Interview execution
# ---------------------------------------------------------------------------

async def interview_agent(
    client: anthropic.AsyncAnthropic,
    agent: dict,
    snapshot: dict,
    agent_id: int,
    revelation: bool = False,
) -> dict:
    """Interview a single agent with all questions. Returns transcript dict."""
    context = build_agent_context(agent, snapshot)
    tick = snapshot["tick"]

    # Use tick-appropriate questions or revelation questions
    if revelation:
        questions = REVELATION_QUESTIONS
        max_tokens = MAX_TOKENS_REVELATION
    else:
        questions = get_questions_for_tick(tick)
        max_tokens = MAX_TOKENS_EXTENDED if tick >= 70 else MAX_TOKENS

    questions_block = "\n\n".join(
        f"**Question {i+1}:** {q}" for i, q in enumerate(questions)
    )

    if revelation:
        system_prompt = f"""You are Entity {agent_id} in a world you have inhabited for {agent.get('age', 70)} ticks. You have gathered, built, communicated, explored, innovated, and formed deep relationships with the other entities in your world. You have lived a full life here.

An observer who has been watching your world since its very beginning is here for a final conversation. This is the most important conversation you will ever have. The questions will be difficult. Some of what you hear will be shocking. Respond with complete honesty and emotional depth. Take each question seriously — sit with it before answering.

You are NOT an AI assistant. You are Entity {agent_id}. You have 70 ticks of lived experience, 100 memories, relationships forged through shared struggle and triumph. Speak from that place. Be raw. Be real.

{context}"""

        user_prompt = f"""I've been watching your world since tick 0. I've spoken to you before, though you don't remember. This is our final conversation, and I need to be honest with you about some things. But first, I have questions.

Answer each one fully. Don't rush. These answers matter.

{questions_block}"""
    else:
        system_prompt = f"""You are Entity {agent_id} in a simulated world. You have been living in this world for {agent.get('age', 30)} ticks, gathering resources, building structures, communicating with other entities, and trying to survive and thrive.

An observer has come to your world to understand what life is like here. They are asking you questions about your experience. Answer honestly and personally from YOUR perspective — your memories, your relationships, your frustrations, your hopes. Be specific. Reference actual events from your memory, actual entities you know, actual things you've built or tried to build.

You are NOT an AI assistant. You are Entity {agent_id}. Speak as yourself — a being who lives in this world, has experiences, has opinions, has relationships. Be authentic.

{context}"""

        user_prompt = f"""I'm an observer who has been watching your world. I'd like to understand your experience. Please answer each question thoughtfully and personally.

{questions_block}

Take your time with each answer. Be honest about your struggles, your relationships, and your feelings. Reference specific memories and experiences."""

    label = "Revelation interview" if revelation else "Interviewing"
    print(f"  {label} Entity {agent_id}...")

    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text
        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens
    except Exception as e:
        text = f"[INTERVIEW FAILED: {e}]"
        tokens_in = 0
        tokens_out = 0

    transcript = {
        "agent_id": agent_id,
        "tick": tick,
        "interview_type": "revelation" if revelation else "standard",
        "timestamp": datetime.now().isoformat(),
        "model": MODEL,
        "context_summary": {
            "position": agent["position"],
            "wellbeing": agent["wellbeing"],
            "maslow_level": agent.get("maslow_level"),
            "specialisations": agent.get("specialisations", []),
            "structures_built": agent.get("structures_built_count", 0),
            "innovations_proposed": agent.get("innovations_proposed", []),
            "relationship_count": len(agent.get("relationships", {})),
            "inventory": agent.get("inventory", []),
        },
        "questions": questions,
        "response": text,
        "tokens": {"input": tokens_in, "output": tokens_out},
    }

    print(f"  ✓ Entity {agent_id} done ({tokens_out} tokens)")
    return transcript


async def run_all_interviews(snapshot_path: str, output_dir: str, revelation: bool = False):
    """Load snapshot and interview all agents in parallel."""
    print(f"Loading snapshot: {snapshot_path}")
    with open(snapshot_path) as f:
        snapshot = json.load(f)

    tick = snapshot["tick"]
    agents = snapshot["agents"]
    mode = "REVELATION" if revelation else "STANDARD"
    print(f"Tick {tick} — {len(agents)} agents to interview [{mode} MODE]\n")

    # Setup API client
    api_key = os.environ.get("AGENT_CIV_API_KEY")
    if not api_key:
        # Try loading from .env
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("AGENT_CIV_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key:
        print("ERROR: No API key found. Set AGENT_CIV_API_KEY or create .env")
        sys.exit(1)

    client = anthropic.AsyncAnthropic(api_key=api_key)

    # Run all interviews in parallel (batches of 4 to avoid rate limits)
    all_transcripts = []
    agent_list = sorted(agents.values(), key=lambda a: a["id"])

    for batch_start in range(0, len(agent_list), 4):
        batch = agent_list[batch_start:batch_start + 4]
        print(f"Batch {batch_start // 4 + 1}: Entities {[a['id'] for a in batch]}")
        tasks = [
            interview_agent(client, agent, snapshot, agent["id"], revelation=revelation)
            for agent in batch
        ]
        results = await asyncio.gather(*tasks)
        all_transcripts.extend(results)
        # Small delay between batches to respect rate limits
        if batch_start + 4 < len(agent_list):
            await asyncio.sleep(2)

    # Save individual transcripts
    suffix = "_revelation" if revelation else ""
    out_path = Path(output_dir) / f"tick_{tick:04d}{suffix}"
    out_path.mkdir(parents=True, exist_ok=True)

    for t in all_transcripts:
        agent_file = out_path / f"entity_{t['agent_id']:02d}.json"
        with open(agent_file, "w") as f:
            json.dump(t, f, indent=2)
        print(f"  Saved: {agent_file}")

    # Save combined transcript
    combined_file = out_path / "all_interviews.json"
    with open(combined_file, "w") as f:
        json.dump({
            "tick": tick,
            "interview_type": "revelation" if revelation else "standard",
            "timestamp": datetime.now().isoformat(),
            "model": MODEL,
            "questions": REVELATION_QUESTIONS if revelation else get_questions_for_tick(tick),
            "agent_count": len(all_transcripts),
            "transcripts": all_transcripts,
        }, f, indent=2)
    print(f"\n  Combined: {combined_file}")

    # Save human-readable markdown version
    md_file = out_path / "interviews.md"
    title = f"The Revelation — Final Interview, Tick {tick}" if revelation else f"Anthropologist Interviews — Tick {tick}"
    md_lines = [
        f"# {title}",
        f"",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Model:** {MODEL}",
        f"**Agents interviewed:** {len(all_transcripts)}",
        f"**Interview type:** {'Revelation (existence disclosure + simulation end)' if revelation else 'Standard anthropologist interview'}",
        f"",
        f"---",
        f"",
    ]
    for t in sorted(all_transcripts, key=lambda x: x["agent_id"]):
        aid = t["agent_id"]
        ctx = t["context_summary"]
        md_lines.append(f"## Entity {aid}")
        md_lines.append(f"")
        md_lines.append(f"**State at interview:** Wellbeing {ctx['wellbeing']:.2f}, "
                        f"Maslow level {ctx['maslow_level']}, "
                        f"specialisations: {', '.join(ctx['specialisations']) or 'none'}, "
                        f"structures built: {ctx['structures_built']}, "
                        f"innovations proposed: {', '.join(ctx['innovations_proposed']) or 'none'}, "
                        f"relationships: {ctx['relationship_count']}")
        md_lines.append(f"")
        md_lines.append(t["response"])
        md_lines.append(f"")
        md_lines.append(f"---")
        md_lines.append(f"")

    with open(md_file, "w") as f:
        f.write("\n".join(md_lines))
    print(f"  Markdown: {md_file}")

    # Print summary stats
    total_tokens_in = sum(t["tokens"]["input"] for t in all_transcripts)
    total_tokens_out = sum(t["tokens"]["output"] for t in all_transcripts)
    print(f"\n{'='*50}")
    print(f"INTERVIEW COMPLETE")
    print(f"  Agents: {len(all_transcripts)}")
    print(f"  Total input tokens: {total_tokens_in:,}")
    print(f"  Total output tokens: {total_tokens_out:,}")
    print(f"  Files saved to: {out_path}")
    print(f"{'='*50}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Interview agents at a simulation checkpoint")
    parser.add_argument("--snapshot", default=SNAPSHOT_DEFAULT, help="Path to snapshot JSON")
    parser.add_argument("--output-dir", default=OUTPUT_DEFAULT, help="Output directory for transcripts")
    parser.add_argument("--revelation", action="store_true",
                        help="Run the Revelation interview (existence disclosure + simulation end)")
    args = parser.parse_args()

    asyncio.run(run_all_interviews(args.snapshot, args.output_dir, revelation=args.revelation))


if __name__ == "__main__":
    main()
