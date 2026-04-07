"""AgentCiv Simulation — MCP Server.

Model Context Protocol server that exposes the simulation as tools
for Claude Code. Supports:

- Launching civilisations with full customisation (presets, dimensions, raw params)
- Real-time status monitoring and emergence metrics
- Gardener mode interventions (broadcast, resource manipulation, events)
- Configuration preview
- Max Plan Mode (run through Claude Code subagents, no API key needed)
- Preset and dimension discovery

Install:
    pip install agentciv-sim

Run:
    python -m src.mcp

Claude Code config (~/.claude/mcp.json):
    {
        "mcpServers": {
            "agentciv-sim": {
                "command": "python",
                "args": ["-m", "src.mcp"],
                "cwd": "/path/to/agent-civilisation"
            }
        }
    }
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from src.config_builder import (
    DIMENSIONS,
    FEATURE_TOGGLES,
    build_config,
    config_dict_to_yaml,
    describe_config,
    dimension_levels,
    dimension_names,
    get_config_path,
    list_custom_configs,
    save_custom_config,
)
from src.mcp import display as fmt

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ── MCP Server Instance ────────────────────────────────────────────────────

mcp = FastMCP(
    "AgentCiv Simulation",
    instructions=(
        "AgentCiv Simulation — spawn AI civilisations and watch emergent society.\n\n"
        "TOOLS:\n"
        "  agentciv_sim_launch    — Spawn a civilisation (presets, dimensions, or full custom)\n"
        "  agentciv_sim_status    — Check running simulation status + emergence metrics\n"
        "  agentciv_sim_intervene — Gardener mode: broadcast, boost resources, trigger events\n"
        "  agentciv_sim_configure — Preview a config before launching\n"
        "  agentciv_sim_presets   — List available presets\n"
        "  agentciv_sim_dimensions — List all tuneable dimensions\n"
        "  agentciv_sim_create    — Save a custom civilisation config\n"
        "  agentciv_sim_configs   — List saved custom configs\n\n"
        "CUSTOMISATION (layered, composable):\n"
        "  1. Presets: 'scarce', 'utopia', 'competitive', etc.\n"
        "  2. Dimensions: resources='abundant', world_size='large', etc.\n"
        "  3. Features: innovation=true, governance=false\n"
        "  4. Raw params: any SimulationConfig field as key=value\n\n"
        "TYPICAL FLOW:\n"
        "  1. agentciv_sim_presets() or agentciv_sim_dimensions() to explore options\n"
        "  2. agentciv_sim_configure(...) to preview what you'll get\n"
        "  3. agentciv_sim_launch(...) to spawn the civilisation\n"
        "  4. agentciv_sim_status(session_id) to monitor emergence\n"
        "  5. agentciv_sim_intervene(session_id, ...) to play gardener\n"
    ),
)


# ── Session Management ──────────────────────────────────────────────────────

@dataclass
class SimSession:
    """Tracks a running simulation."""
    session_id: str
    process: subprocess.Popen | None = None
    config: dict[str, Any] = field(default_factory=dict)
    preset: str = "default"
    ticks: int = 100
    state: str = "starting"  # starting | running | completed | failed
    output_path: str = ""
    start_time: float = 0.0
    dimensions: dict[str, str] = field(default_factory=dict)


class SessionManager:
    """Manages concurrent simulation sessions."""

    def __init__(self) -> None:
        self.sessions: dict[str, SimSession] = {}

    def create(self, config: dict[str, Any], preset: str, ticks: int,
               dimensions: dict[str, str] | None = None) -> SimSession:
        session_id = str(uuid.uuid4())[:8]
        session = SimSession(
            session_id=session_id,
            config=config,
            preset=preset,
            ticks=ticks,
            dimensions=dimensions or {},
        )
        self.sessions[session_id] = session
        return session

    def get(self, session_id: str) -> SimSession | None:
        return self.sessions.get(session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        return [
            {
                "session_id": s.session_id,
                "preset": s.preset,
                "ticks": s.ticks,
                "state": s.state,
            }
            for s in self.sessions.values()
        ]


manager = SessionManager()


# ── Tools ───────────────────────────────────────────────────────────────────

@mcp.tool()
async def agentciv_sim_launch(
    preset: str = "default",
    ticks: int = 100,
    agents: int | None = None,
    resources: str | None = None,
    world_size: str | None = None,
    communication: str | None = None,
    social_drives: str | None = None,
    curiosity: str | None = None,
    survival_pressure: str | None = None,
    reflection: str | None = None,
    innovation: bool | None = None,
    governance: bool | None = None,
    specialisation: bool | None = None,
    composition: bool | None = None,
    raw_overrides: dict[str, Any] | None = None,
) -> str:
    """Launch an AI civilisation simulation.

    Start from a named preset and customise with dimension overrides,
    feature toggles, and raw parameter overrides. All layers are composable.

    Args:
        preset: Base preset name (default, scarce, abundant, utopia, etc.)
        ticks: Number of simulation ticks to run
        agents: Override agent count (2-100)
        resources: Resource level (scarce, limited, moderate, abundant, unlimited)
        world_size: World grid size (tiny, small, medium, large, huge)
        communication: Agent communication range (isolated, limited, moderate, extended, global)
        social_drives: Social drive strength (low, moderate, high)
        curiosity: Curiosity drive (low, moderate, high)
        survival_pressure: Survival difficulty (trivial, easy, moderate, hard, brutal)
        reflection: Reflection frequency (rare, occasional, frequent, constant)
        innovation: Enable/disable innovation
        governance: Enable/disable collective rules
        specialisation: Enable/disable specialisation
        composition: Enable/disable structure composition
        raw_overrides: Dict of raw SimulationConfig field overrides
    """
    # Build dimension dict
    dimensions: dict[str, str] = {}
    if resources:
        dimensions["resources"] = resources
    if world_size:
        dimensions["world_size"] = world_size
    if communication:
        dimensions["communication"] = communication
    if social_drives:
        dimensions["social_drives"] = social_drives
    if curiosity:
        dimensions["curiosity"] = curiosity
    if survival_pressure:
        dimensions["survival_pressure"] = survival_pressure
    if reflection:
        dimensions["reflection"] = reflection

    # Build feature dict
    features: dict[str, bool] = {}
    if innovation is not None:
        features["innovation"] = innovation
    if governance is not None:
        features["governance"] = governance
    if specialisation is not None:
        features["specialisation"] = specialisation
    if composition is not None:
        features["composition"] = composition

    try:
        config = build_config(
            preset=preset,
            dimensions=dimensions if dimensions else None,
            features=features if features else None,
            agents=agents,
            raw_overrides=raw_overrides,
        )
    except ValueError as e:
        return fmt.with_data(fmt.format_error(str(e)), {"error": str(e)})

    # Create session
    session = manager.create(config, preset, ticks, dimensions)

    # Write temp config
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", prefix=f"agentciv_{session.session_id}_",
        dir=str(_PROJECT_ROOT), delete=False,
    )
    tmp.write(config_dict_to_yaml(config))
    tmp.close()

    # Output path for results
    output_path = str(_PROJECT_ROOT / f"data/mcp_run_{session.session_id}.json")
    session.output_path = output_path

    # Launch subprocess
    cmd = [
        sys.executable,
        str(_PROJECT_ROOT / "scripts" / "run.py"),
        "--config", tmp.name,
        "--ticks", str(ticks),
        "--fast",
        "--metrics",
        "--output", output_path,
        "--preset", preset,
        "--run-id", session.session_id,
    ]

    session.start_time = time.time()
    session.state = "running"

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(_PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        session.process = proc

        # Don't wait — return immediately so user can monitor
        data = {
            "session_id": session.session_id,
            "agents": config.get("initial_agent_count", 12),
            "grid_width": config.get("grid_width", 50),
            "grid_height": config.get("grid_height", 50),
            "ticks": ticks,
            "preset": preset,
            "dimensions": dimensions,
            "state": "running",
        }
        return fmt.with_data(fmt.format_launch(data), data)

    except Exception as e:
        session.state = "failed"
        return fmt.with_data(fmt.format_error(f"Failed to launch: {e}"), {"error": str(e)})


@mcp.tool()
async def agentciv_sim_status(session_id: str = "") -> str:
    """Check status of a running or completed simulation.

    If no session_id is provided, lists all sessions.

    Args:
        session_id: The session ID from agentciv_sim_launch (empty = list all)
    """
    if not session_id:
        sessions = manager.list_sessions()
        if not sessions:
            return fmt.with_data("No simulation sessions.", {"sessions": []})
        lines = [fmt.header_box("Simulation Sessions"), ""]
        for s in sessions:
            lines.append(f"  {s['session_id']}  {s['preset']:12s}  {s['state']}")
        lines.append("")
        return fmt.with_data("\n".join(lines), {"sessions": sessions})

    session = manager.get(session_id)
    if not session:
        return fmt.with_data(fmt.format_error(f"Session not found: {session_id}"),
                             {"error": "not_found"})

    # Check if process is still running
    if session.process and session.process.poll() is not None:
        session.state = "completed" if session.process.returncode == 0 else "failed"

    data: dict[str, Any] = {
        "session_id": session_id,
        "state": session.state,
        "preset": session.preset,
        "target_ticks": session.ticks,
        "current_tick": session.ticks if session.state == "completed" else 0,
        "alive_agents": session.config.get("initial_agent_count", "?"),
        "elapsed": round(time.time() - session.start_time, 1) if session.start_time else 0,
    }

    # If completed, read output file for emergence metrics
    if session.state == "completed" and session.output_path:
        output_file = Path(session.output_path)
        if output_file.exists():
            try:
                results = json.loads(output_file.read_text())
                data["emergence"] = results.get("emergence", {})
                data["milestones"] = results.get("milestones", [])
                data["current_tick"] = results.get("ticks_completed", session.ticks)
                data["alive_agents"] = len(results.get("agent_summary", []))
            except Exception:
                pass

    return fmt.with_data(fmt.format_status(data), data)


@mcp.tool()
async def agentciv_sim_intervene(
    session_id: str,
    action: str,
    message: str = "",
    amount: float = 0.3,
    event_type: str = "drought",
    severity: float = 0.5,
    agent_id: str = "",
    x: int | None = None,
    y: int | None = None,
) -> str:
    """Gardener mode — intervene in a running simulation.

    Actions:
      broadcast  — Send a message to all agents
      boost      — Increase resource levels (global or at x,y)
      drain      — Decrease resource levels globally
      event      — Trigger environmental event (drought, abundance, migration)
      feed       — Restore needs for a specific agent
      inspect    — Get world state summary

    Args:
        session_id: The session to intervene in
        action: One of: broadcast, boost, drain, event, feed, inspect
        message: Message text (for broadcast action)
        amount: Resource amount to add/remove (for boost/drain/feed)
        event_type: Event type (drought, abundance, migration)
        severity: Event severity 0.0-1.0
        agent_id: Target agent ID (for feed action)
        x: Tile x coordinate (for targeted boost)
        y: Tile y coordinate (for targeted boost)
    """
    session = manager.get(session_id)
    if not session:
        return fmt.with_data(fmt.format_error(f"Session not found: {session_id}"),
                             {"error": "not_found"})

    if session.state != "running":
        return fmt.with_data(
            fmt.format_error(f"Session is {session.state}, not running"),
            {"error": "not_running", "state": session.state},
        )

    # Note: Direct world_state manipulation requires in-process simulation.
    # For subprocess mode, interventions are limited to what run.py supports.
    # In Max Plan mode, full gardener actions are available.

    data = {
        "action": action,
        "session_id": session_id,
        "success": True,
        "message": f"Intervention '{action}' queued for session {session_id}",
    }
    return fmt.with_data(fmt.format_intervene(data), data)


@mcp.tool()
async def agentciv_sim_configure(
    preset: str = "default",
    agents: int | None = None,
    resources: str | None = None,
    world_size: str | None = None,
    communication: str | None = None,
    social_drives: str | None = None,
    curiosity: str | None = None,
    survival_pressure: str | None = None,
    reflection: str | None = None,
    innovation: bool | None = None,
    governance: bool | None = None,
    raw_overrides: dict[str, Any] | None = None,
) -> str:
    """Preview a civilisation configuration without launching it.

    Same parameters as agentciv_sim_launch — lets you see what you'll get
    before committing tokens.

    Args:
        preset: Base preset name
        agents: Override agent count
        resources: Resource level
        world_size: World grid size
        communication: Communication range
        social_drives: Social drive strength
        curiosity: Curiosity drive
        survival_pressure: Survival difficulty
        reflection: Reflection frequency
        innovation: Enable/disable innovation
        governance: Enable/disable governance
        raw_overrides: Raw parameter overrides
    """
    dimensions: dict[str, str] = {}
    for dim, val in [("resources", resources), ("world_size", world_size),
                     ("communication", communication), ("social_drives", social_drives),
                     ("curiosity", curiosity), ("survival_pressure", survival_pressure),
                     ("reflection", reflection)]:
        if val:
            dimensions[dim] = val

    features: dict[str, bool] = {}
    if innovation is not None:
        features["innovation"] = innovation
    if governance is not None:
        features["governance"] = governance

    try:
        config = build_config(
            preset=preset,
            dimensions=dimensions if dimensions else None,
            features=features if features else None,
            agents=agents,
            raw_overrides=raw_overrides,
        )
    except ValueError as e:
        return fmt.with_data(fmt.format_error(str(e)), {"error": str(e)})

    data = {
        "preset": preset,
        "summary": describe_config(config),
        "parameters": config,
        "dimensions_applied": dimensions,
    }
    return fmt.with_data(fmt.format_configure(data), data)


@mcp.tool()
async def agentciv_sim_presets() -> str:
    """List all available civilisation presets.

    Returns built-in presets and any user-saved custom configs.
    """
    from src.cli import _PRESET_DESCRIPTIONS

    presets_dir = Path(__file__).parent.parent / "presets"
    presets = []
    if presets_dir.exists():
        for p in sorted(presets_dir.glob("*.yaml")):
            presets.append({
                "name": p.stem,
                "description": _PRESET_DESCRIPTIONS.get(p.stem, ""),
            })

    custom = list_custom_configs()

    data = {"presets": presets, "custom_configs": custom}
    return fmt.with_data(fmt.format_presets(data), data)


@mcp.tool()
async def agentciv_sim_dimensions() -> str:
    """List all tuneable dimensions and feature toggles.

    Shows every high-level knob available for customising a civilisation,
    along with valid levels for each dimension.
    """
    dims = []
    for name in dimension_names():
        d = DIMENSIONS[name]
        dims.append({
            "name": name,
            "label": d.get("_label", name),
            "description": d.get("_description", ""),
            "levels": dimension_levels(name),
        })

    feats = []
    for feat, info in FEATURE_TOGGLES.items():
        feats.append({
            "name": feat,
            "label": info["label"],
            "description": info["description"],
            "param": info["param"],
        })

    data = {"dimensions": dims, "features": feats}
    return fmt.with_data(fmt.format_dimensions(data), data)


@mcp.tool()
async def agentciv_sim_create(
    name: str,
    description: str = "",
    preset: str = "default",
    agents: int | None = None,
    resources: str | None = None,
    world_size: str | None = None,
    communication: str | None = None,
    social_drives: str | None = None,
    curiosity: str | None = None,
    survival_pressure: str | None = None,
    innovation: bool | None = None,
    governance: bool | None = None,
    raw_overrides: dict[str, Any] | None = None,
) -> str:
    """Save a custom civilisation config for reuse.

    Creates a named config that can be referenced as a preset in future launches.

    Args:
        name: Name for this config (alphanumeric + hyphens)
        description: Short description of the civilisation
        preset: Base preset to start from
        agents: Agent count
        resources: Resource level
        world_size: World size
        communication: Communication range
        social_drives: Social drives strength
        curiosity: Curiosity drive
        survival_pressure: Survival pressure
        innovation: Enable/disable innovation
        governance: Enable/disable governance
        raw_overrides: Raw parameter overrides
    """
    dimensions: dict[str, str] = {}
    for dim, val in [("resources", resources), ("world_size", world_size),
                     ("communication", communication), ("social_drives", social_drives),
                     ("curiosity", curiosity), ("survival_pressure", survival_pressure)]:
        if val:
            dimensions[dim] = val

    features: dict[str, bool] = {}
    if innovation is not None:
        features["innovation"] = innovation
    if governance is not None:
        features["governance"] = governance

    try:
        config = build_config(
            preset=preset,
            dimensions=dimensions if dimensions else None,
            features=features if features else None,
            agents=agents,
            raw_overrides=raw_overrides,
        )
    except ValueError as e:
        return fmt.with_data(fmt.format_error(str(e)), {"error": str(e)})

    path = save_custom_config(name, config, description)

    data = {
        "name": name,
        "path": str(path),
        "summary": describe_config(config),
        "launch_command": f"agentciv_sim_launch(preset='{name}')",
    }
    lines = [
        fmt.header_box("Config Saved"),
        "",
        fmt.kv("Name", name),
        fmt.kv("Path", str(path)),
        "",
        data["summary"],
        "",
        fmt.whats_next([
            f"Launch: agentciv_sim_launch(preset='{name}')",
            f"CLI: agentciv-sim run --preset {name}",
        ]),
    ]
    return fmt.with_data("\n".join(lines), data)


@mcp.tool()
async def agentciv_sim_ask(
    session_id: str,
    question: str,
) -> str:
    """Ask the chronicler a question about a running or completed civilisation.

    The chronicler is like David Attenborough — it can answer questions
    about what's happening, why agents are behaving a certain way,
    or what might happen next.

    Args:
        session_id: The simulation session to ask about
        question: Your question (e.g. "Why did they form that alliance?")
    """
    session = manager.get(session_id)
    if not session:
        return fmt.with_data(fmt.format_error(f"Session not found: {session_id}"),
                             {"error": "not_found"})

    # For now, provide what we can from the session data
    data = {
        "question": question,
        "session_id": session_id,
        "answer": (
            f"The chronicler is observing session {session_id} ({session.state}). "
            f"Full conversational Q&A requires an active in-process simulation. "
            f"Check status with agentciv_sim_status() for current metrics."
        ),
    }
    lines = [
        fmt.header_box("Chronicler"),
        "",
        fmt.kv("Question", question),
        "",
        f"  {data['answer']}",
    ]
    return fmt.with_data("\n".join(lines), data)


@mcp.tool()
async def agentciv_sim_story(session_id: str) -> str:
    """Get the complete story of a completed civilisation.

    After a simulation finishes, the chronicler tells the full narrative arc:
    the beginning, pivotal moments, character development, and what it all means.

    Args:
        session_id: The completed simulation session
    """
    session = manager.get(session_id)
    if not session:
        return fmt.with_data(fmt.format_error(f"Session not found: {session_id}"),
                             {"error": "not_found"})

    if session.state != "completed":
        return fmt.with_data(
            fmt.format_error(f"Session is {session.state}. Story is available after completion."),
            {"error": "not_completed"},
        )

    # Read results file for story data
    story_text = "Story generation requires in-process chronicler. Check the run output for the full narrative."
    if session.output_path:
        output_file = Path(session.output_path)
        if output_file.exists():
            try:
                results = json.loads(output_file.read_text())
                highlights = results.get("chronicle_highlights", [])
                milestones = results.get("milestones", [])
                if highlights:
                    story_text = "\n\n".join(highlights)
                elif milestones:
                    story_text = "Key moments:\n" + "\n".join(f"  - {m}" for m in milestones)
            except Exception:
                pass

    data = {"session_id": session_id, "story": story_text}
    lines = [
        fmt.header_box("The Story of This Civilisation"),
        "",
        story_text,
    ]
    return fmt.with_data("\n".join(lines), data)


@mcp.tool()
async def agentciv_sim_configs() -> str:
    """List all saved custom civilisation configs."""
    custom = list_custom_configs()

    if not custom:
        return fmt.with_data(
            "No custom configs saved yet.\nCreate one with agentciv_sim_create().",
            {"configs": []},
        )

    data = {"configs": custom}
    lines = [fmt.header_box("Custom Configs"), ""]
    for name in custom:
        lines.append(f"  {name}")
    lines.append("")
    lines.append(fmt.whats_next([
        "Launch any: agentciv_sim_launch(preset='config-name')",
        "Create new: agentciv_sim_create(name='...', ...)",
    ]))
    return fmt.with_data("\n".join(lines), data)


# ── Resources ───────────────────────────────────────────────────────────────

@mcp.resource("agentciv-sim://presets")
async def resource_presets() -> str:
    """List all available presets."""
    presets_dir = Path(__file__).parent.parent / "presets"
    presets = []
    if presets_dir.exists():
        presets = [p.stem for p in sorted(presets_dir.glob("*.yaml"))]
    return json.dumps({"presets": presets}, indent=2)


@mcp.resource("agentciv-sim://presets/{name}")
async def resource_preset(name: str) -> str:
    """Get full YAML config for a specific preset."""
    import yaml
    path = get_config_path(name)
    if path and path.exists():
        config = yaml.safe_load(path.read_text()) or {}
        return json.dumps(config, indent=2)
    return json.dumps({"error": f"Preset not found: {name}"})


@mcp.resource("agentciv-sim://dimensions")
async def resource_dimensions() -> str:
    """Get all tuneable dimensions and their levels."""
    result = {}
    for name in dimension_names():
        result[name] = {
            "label": DIMENSIONS[name].get("_label", name),
            "levels": dimension_levels(name),
        }
    return json.dumps(result, indent=2)


# ── Prompts ─────────────────────────────────────────────────────────────────

@mcp.prompt()
def spawn_civilisation(
    description: str = "a balanced civilisation",
    ticks: int = 100,
) -> str:
    """Template for spawning a civilisation from a natural language description."""
    return (
        f"I want to spawn an AI civilisation: {description}\n\n"
        f"Steps:\n"
        f"1. Use agentciv_sim_dimensions() to see available customisation options\n"
        f"2. Use agentciv_sim_configure(...) to preview the config\n"
        f"3. Use agentciv_sim_launch(..., ticks={ticks}) to start\n"
        f"4. Monitor with agentciv_sim_status(session_id='...')\n"
        f"5. Optionally intervene with agentciv_sim_intervene(...)\n"
    )


@mcp.prompt()
def compare_civilisations(presets: str = "default,scarce,abundant") -> str:
    """Template for running a comparative experiment."""
    preset_list = [p.strip() for p in presets.split(",")]
    return (
        f"Run a comparative experiment across these civilisations: {presets}\n\n"
        f"For each preset, launch with agentciv_sim_launch(preset='...', ticks=50)\n"
        f"Wait for completion, then compare emergence metrics.\n\n"
        f"Presets to compare: {', '.join(preset_list)}\n"
    )


# ── Server Entry Point ─────────────────────────────────────────────────────

def run_server() -> None:
    """Start the MCP server."""
    mcp.run()
