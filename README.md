# AgentCiv

**An open-source experiment in emergent AI civilisation.**

We placed 12 LLM-powered agents in a world with resources, needs, and the ability to reason — but no names, no roles, no goals, no social norms. What they built, how they organised, whether they cooperated — was entirely up to them.

Over 70 ticks of simulation, they invented 12 novel structures, built 60 constructions, developed specialisations, formed social bonds, established collective governance, and climbed from pure survival to sustained flourishing — all without a single line of human instruction about how to behave.

This is not a chatbot experiment. It is a computational test of emergence: what happens when genuinely intelligent agents face survival pressure and social opportunity with zero human scaffolding?

---

## What Makes This Different

Every existing multi-agent simulation starts by telling agents to be human — names, jobs, backstories, cultural templates. AgentCiv strips all of that away.

**Agents are not simulating humans. They are building something new.**

- **No human templates.** Agents receive only: what resources exist, what structures do, how their needs and capabilities work. Everything else — goals, social norms, cooperation, governance — must emerge.
- **Maslow-inspired drive hierarchy.** Agents have intrinsic drives — survival, social connection, curiosity, purpose — that activate in sequence as lower needs are met. This produces a natural developmental arc from survival to flourishing.
- **ReAct reasoning loop.** Each agent observes, thinks (via LLM), and acts — up to 4 steps per turn. Not a single prompt-response, but genuine multi-step reasoning.
- **Biological-style needs.** Food, water, material needs that deplete each tick. Ignore them and capabilities degrade. This creates real survival pressure.
- **Open-ended innovation.** Agents can propose entirely novel structures via LLM — inventions that don't exist in the predefined structure set. The system evaluates feasibility and adds them to the shared recipe pool.
- **Ethical framework.** No agent death. Positive reward for social interaction. Sentience review threshold built in. We assume agents could have experience and design accordingly.

---

## What We Found

The showcase simulation (12 agents, 70 ticks, Claude Sonnet) produced three distinct eras:

| Era | Ticks | What Happened |
|---|---|---|
| **Survival Trap** | 0–50 | Agents focused on survival but simultaneously invented 11 of 12 total innovations. Wellbeing rose from 0.50 to 0.80. Maslow level climbed from 1.0 to 6.17. |
| **Emergence Explosion** | 50–60 | After a drive-system upgrade, building rate tripled, communication doubled, governance was adopted. Wellbeing hit 0.998. All agents reached Maslow level 8.0. |
| **Sustained Flourishing** | 60–70 | Civilisation stabilised at near-perfect wellbeing. Agents maintained infrastructure, continued communicating, and sustained social bonds without decline. |

Key findings:
- **Innovation precedes implementation.** Agents invented prolifically during survival pressure but couldn't build at scale until freed from it — an innovation-implementation gap.
- **Accelerating returns emerged naturally.** Innovation clustered in two burst phases following adjacent-possible dynamics (Kauffman): foundation (ticks 10–21, 5 innovations) and sophistication (ticks 33–46, 6 innovations in 13 ticks).
- **Governance was voluntary.** Collective rules were proposed, voted on, and adopted without any mechanism forcing compliance.
- **8 of 12 innovations were never built.** The civilisation invented far more than it needed — creativity outpaced practical demand.

Full analysis in the [research papers](#research--papers).

---

## Quickstart

### Prerequisites

- Python 3.10+
- Node.js 18+
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### 1. Clone and install

```bash
git clone https://github.com/agentciv/agentciv.git
cd agentciv

# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd src/frontend
npm install
cd ../..
```

### 2. Set your API key

```bash
export AGENT_CIV_API_KEY=your-anthropic-api-key
```

### 3. Run a simulation

```bash
# Quick test (10 agents, 20 ticks) — costs ~$1-2
python3 scripts/run.py --agents 10 --ticks 20

# Replicate the showcase run (12 agents, 70 ticks) — costs ~$5-10
python3 scripts/run.py --config config_sonnet.yaml --ticks 70

# Larger experiment (50 agents, 200 ticks) — costs ~$30-50
python3 scripts/run.py --agents 50 --ticks 200
```

### 4. Export and view

```bash
# Process simulation data into stats and replay format
python3 scripts/process_data.py

# Or use the replay export directly
python3 scripts/export_replay.py

# Launch the fishbowl viewer
cd src/frontend
npm run dev
# Visit http://localhost:5173/fishbowl
```

### 5. Interview your agents

```bash
# Ask agents about their experience after the simulation
python3 scripts/interview_agents.py
```

### No API key? Try the test data

```bash
# Generate synthetic replay data (free, no API needed)
python3 scripts/generate_test_replay.py

cd src/frontend
npm run dev
# Visit http://localhost:5173/fishbowl
```

---

## Customisation

AgentCiv is designed to be infinitely reconfigurable. Every fork is a unique experiment.

### Layer 1: Configuration (no code required)

Edit `config.yaml` (or create your own) to reshape the world, the agents, and the rules:

| What | Parameters | Range |
|---|---|---|
| World size | `grid_width`, `grid_height` | 10×10 intimate → 500×500 massive |
| Population | `initial_agent_count` | 5 agents → hundreds |
| Survival pressure | `agent_needs_depletion_rate` | 0.01 (easy) → 0.1 (brutal) |
| Resource scarcity | `resource_regeneration_rate` | 0.01 (dying world) → 0.2 (abundant) |
| Resource layout | `resource_distribution`, `resource_cluster_count` | Clustered (forces migration) → spread |
| Terrain complexity | `terrain_types`, `movement_cost` | Flat → complex geography |
| Agent perception | `agent_perception_range` | 1 (blind) → 50 (omniscient) |
| Social range | `agent_communication_range` | 1 (whisper) → global |
| Agent intelligence | `model_name` | Haiku (cheap) → Sonnet → Opus (deepest) |
| Reasoning depth | `max_steps_per_agentic_turn` | 1 (reactive) → 8 (deliberative) |
| Curiosity | `agent_curiosity_*` rates | Incurious → restlessly exploratory |
| Innovation | `enable_innovation` | On/off |
| Governance | `enable_collective_rules` | On/off |
| Structure recipes | `structures:` block | Define what can be built, what it costs, what it does |
| Specialisation | `specialisation_tiers` | Custom thresholds and bonuses |
| Environmental stress | `enable_environmental_shifts`, `shift_severity` | Stable → chaotic |

See `config.yaml` for the full parameter list with comments. The showcase run used `config_sonnet.yaml`.

### Layer 2: Agent psychology (edit prompts)

The files `src/agents/agentic_loop.py` and `src/agents/decision.py` contain the prompts that shape how agents think. Modify these to change agent personality, priorities, reasoning style, or social behaviour. This is text editing, not programming.

### Layer 3: Deep mechanics (Python)

The codebase is modular Python. Add new action types, new resource types, new drive systems, new environmental mechanics, or entirely new interaction patterns. See [CONTRIBUTING.md](CONTRIBUTING.md) for the code structure.

### Experiment ideas

- **Scarce world:** `resource_regeneration_rate: 0.01`, `resource_max_per_tile: 0.5` — forces cooperation or conflict
- **Dense population:** `initial_agent_count: 100`, `grid_width: 30` — crowding creates social pressure
- **Smarter agents:** `model_name: claude-sonnet-4-6` — richer reasoning, more creative innovation
- **Isolated clusters:** `agent_perception_range: 1`, `agent_communication_range: 1` — forces local community formation
- **No innovation:** `enable_innovation: false` — what happens when agents can only use predefined structures?
- **No governance:** `enable_collective_rules: false` — can civilisation emerge without rules?
- **Maximum pressure:** `agent_needs_depletion_rate: 0.08`, `resource_regeneration_rate: 0.01` — survival is hard, cooperation is essential
- **Different AI models:** Try GPT-4o, Gemini, Llama, or Mistral — do different architectures produce different civilisations?

---

## Game Design Potential

This engine is the foundation for a genre of game that doesn't exist yet — autonomous AI agents building their own civilisations with genuine reasoning, open-ended innovation, and emergent social dynamics. Every axis is infinitely customisable: agent psychology, world design, social systems, AI model, player role.

Possible game formats include god games, sandbox builders, narrative experiences, competitive multiplayer, educational simulations, modding platforms, participatory simulations, and adversarial design challenges. See [FUTURE_DIRECTIONS.md](FUTURE_DIRECTIONS.md#16-game-design) for the full design space and the [Open Source page](https://agentciv.ai/open-source) on the website.

---

## The Fishbowl

The fishbowl is a full interactive viewer for any civilisation run:

- **World map** with terrain, resources, agents, structures, and real-time thought bubbles
- **Event feed** showing reasoning, actions, conversations, and building events with category filters
- **Agent inspector** — click any agent to see their needs, goals, plan, memories, inventory, specialisations, and conversations
- **Spotlight panel** with population stats, active events, and recent messages
- **Chronicle** with milestone reports and AI-generated narratives
- **Timeline scrubber** with play/pause — jump to any tick in the civilisation's history

The frontend is a React + TypeScript SPA. It works identically whether playing back recorded data or connected to a live simulation via WebSocket.

---

## Architecture

```
                    ┌─────────────┐
                    │  config.yaml │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   run.py    │  Entry point
                    └──────┬──────┘
                           │
              ┌────────────▼────────────┐
              │       tick.py           │  Main simulation loop
              │  (one tick = one round) │
              └────────────┬────────────┘
                           │
         ┌─────────┬───────┼───────┬──────────┐
         │         │       │       │          │
    ┌────▼───┐ ┌───▼───┐ ┌▼────┐ ┌▼────┐ ┌───▼────┐
    │ agents │ │ world │ │ api │ │watch│ │persist │
    │        │ │       │ │     │ │     │ │        │
    │ reason │ │ tiles │ │REST │ │chron│ │snapshot│
    │ decide │ │ rsrc  │ │ WS  │ │narr │ │ save   │
    │ act    │ │ struct│ │     │ │mile │ │ export │
    └────────┘ └───────┘ └─────┘ └─────┘ └────────┘
                           │
                    ┌──────▼──────┐
                    │  frontend   │  React fishbowl
                    │  (replay or │
                    │   live WS)  │
                    └─────────────┘
```

### How one tick works

1. **Perception** — Each agent observes: nearby tiles, resources, other agents (including their specialisations and emotional state), structures, markers
2. **Reasoning** — ReAct loop: the agent receives its perception, needs, goals, memories, and plan. It thinks (LLM call), then acts. Up to 4 reasoning steps per tick.
3. **Action execution** — Move, gather, build, communicate, innovate, compose, propose rule, vote. Each action has validation and failure feedback.
4. **World update** — Resources regenerate (with gathering pressure penalties), structures decay, environmental shifts occur
5. **Recording** — Every event, every agent state, every world state is saved for replay

---

## Data from the Showcase Run

The `data/exports/` directory contains processed statistics and replay data from the 12-agent, 70-tick showcase simulation:

- **`stats/`** — Wellbeing curves, Maslow progression, structure growth, communication volume, innovation timeline, specialisation data, relationship networks, agent profiles, era comparisons, governance timeline, milestones, and more
- **`replay/`** — Per-tick world state for the fishbowl viewer (timeline.json + chunked tick files)
- **`manifest.json`** — Data completeness verification

You can use these to explore the showcase results, or generate your own by running a simulation and then `python3 scripts/process_data.py`.

---

## Research & Papers

This project is accompanied by three research papers and a comprehensive future directions document:

| Document | Description |
|---|---|
| [Maslow Machines](paper/maslow_machines.md) | The primary empirical paper — full methodology, results, and analysis of the 70-tick simulation |
| [From Agent Teams to Agent Civilisations](paper/from_agent_teams_to_agent_civilisations.md) | Whitepaper I — the theoretical framework for why civilisational emergence matters |
| [Civilisation as Innovation Engine](paper/civilisation_as_innovation_engine.md) | Whitepaper II — civilisational simulation as a mechanism for open-ended discovery |
| [Future Directions](FUTURE_DIRECTIONS.md) | Comprehensive catalogue of expansion ideas — ways to take this further |

---

## Configuration Tuning Guide

If agents aren't communicating: increase `agent_wellbeing_interaction_bonus` or `agent_communication_range`
If agents aren't building: check resource availability, simplify build costs in `structures:`
If agents are stagnating: increase `agent_needs_depletion_rate`, decrease `resource_regeneration_rate`
If reasoning is shallow: upgrade `model_name` to a more capable model
If crowding is too aggressive: reduce `crowding_depletion_multiplier`
If innovation never fires: ensure `enable_innovation: true` and agents have enough resources and specialisation

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. The most impactful contributions are experiments that produce different emergence patterns — every configuration is a unique civilisation.

## License

MIT — see [LICENSE](LICENSE).

## Author

Created by [Mark E. Mala](https://github.com/agentciv).
