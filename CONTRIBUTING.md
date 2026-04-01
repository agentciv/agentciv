# Contributing to AgentCiv

We welcome contributions. Whether you're fixing a bug, improving documentation, tuning parameters, or building entirely new emergence mechanics — this project is designed for experimentation.

## Getting Started

1. Fork the repo and clone it locally
2. Follow the [setup instructions](README.md#quickstart) to get both the simulation and frontend running
3. Make your changes on a feature branch
4. Submit a pull request with a clear description of what you changed and why

## Project Structure

```
agentciv/
  config.yaml                 # All simulation parameters (start here)
  src/
    agents/
      agent.py                # Agent state and lifecycle
      agentic_loop.py         # ReAct reasoning loop (observe → think → act)
      decision.py             # Action selection and validation
      communication.py        # Agent-to-agent messaging
      innovation.py           # Novel structure proposal via LLM
      specialisation.py       # Activity-based skill acquisition
      memory.py               # Memory storage and retrieval
      perception.py           # What agents can see
      llm.py                  # LLM API wrapper
    engine/
      world.py                # Grid, tiles, resources
      environment.py          # Resource dynamics, terrain effects
      structures.py           # Building and structure management
      composition.py          # Combining structures into higher-tier ones
      feedback.py             # Action failure reporting
      persistence.py          # State save/load, snapshot recording
      tick.py                 # Main simulation loop (one tick)
    watcher/                  # Chronicler — observes and narrates
    api/                      # FastAPI REST + WebSocket server
    frontend/                 # React + TypeScript fishbowl UI
  scripts/
    run.py                    # Main entry point for running simulations
    export_replay.py          # Converts raw recordings to frontend format
    process_data.py           # Generates statistics and replay data from simulation
    interview_agents.py       # Post-simulation agent interviews
    generate_test_replay.py   # Synthetic test data generator
```

## What to Work On

**Tune the world.** The most impactful contributions are parameter changes in `config.yaml` that produce richer emergence. Try:
- Different resource distributions and depletion rates
- Varying agent counts and perception ranges
- Adjusted need depletion (more survival pressure = more cooperation)
- Different LLM models (Haiku vs Sonnet vs other providers)

**Improve agent reasoning.** The prompts in `agentic_loop.py` and `decision.py` shape how agents think. Better prompts produce richer behaviour.

**Add emergence mechanics.** New structure types, new interaction patterns, new environmental dynamics, new resource types, new drive systems. The architecture is designed to be extensible.

**Run your own experiments.** Run simulations with different configs, process the data with `scripts/process_data.py`, and share your findings. Every configuration produces a different civilisation.

**Frontend improvements.** The fishbowl UI is React + TypeScript + Tailwind. Visualisation improvements, new inspection tools, better mobile support.

**See [FUTURE_DIRECTIONS.md](FUTURE_DIRECTIONS.md)** for a comprehensive catalogue of expansion ideas — from 3D worlds and agent reproduction to multi-civilisation first contact and mixed-model ecosystems. And those are just the ones we've thought of.

## Code Guidelines

- Python: follow existing style (type hints, docstrings on public functions)
- TypeScript: strict mode, no `any` types
- Keep changes focused — one feature or fix per PR
- Test your changes: run a short simulation (10 agents, 10 ticks) and verify the frontend replays correctly

## Running a Test Simulation

```bash
# Generate synthetic replay data (no API key needed)
python3 scripts/generate_test_replay.py

# Or run a real simulation (requires API key)
export AGENT_CIV_API_KEY=your-anthropic-key
python3 scripts/run.py --agents 10 --ticks 20

# Export to replay format
python3 scripts/export_replay.py

# View in browser
cd src/frontend && npm run dev
```

## Questions?

Open an issue. We're happy to help.
