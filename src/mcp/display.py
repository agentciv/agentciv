"""Display formatting for MCP tool responses.

Produces beautiful, readable output for Claude Code.
Every response has a human-readable section + embedded JSON for programmatic access.
"""

from __future__ import annotations

import json
from typing import Any


def with_data(formatted: str, data: dict[str, Any]) -> str:
    """Combine human-readable text with embedded JSON data."""
    return f"{formatted}\n\n```json\n{json.dumps(data, indent=2, default=str)}\n```"


def header_box(title: str, subtitle: str = "") -> str:
    """Draw a header box."""
    width = max(len(title), len(subtitle)) + 4
    top = f"╔{'═' * width}╗"
    mid_title = f"║ {title:^{width - 2}} ║"
    bot = f"╚{'═' * width}╝"
    if subtitle:
        mid_sub = f"║ {subtitle:^{width - 2}} ║"
        return f"{top}\n{mid_title}\n{mid_sub}\n{bot}"
    return f"{top}\n{mid_title}\n{bot}"


def section(title: str) -> str:
    """Section header."""
    return f"\n── {title} {'─' * max(1, 50 - len(title))}"


def kv(key: str, value: Any) -> str:
    """Key-value line."""
    return f"  {key}: {value}"


def status(ok: bool, msg: str) -> str:
    """Status line with checkmark or cross."""
    icon = "✓" if ok else "✗"
    return f"  {icon} {msg}"


def tip(text: str) -> str:
    """Contextual suggestion."""
    return f"  ✦ {text}"


def whats_next(items: list[str]) -> str:
    """Guidance block."""
    lines = [section("What's next")]
    for item in items:
        lines.append(f"  → {item}")
    return "\n".join(lines)


def table(headers: list[str], rows: list[list[Any]]) -> str:
    """Simple markdown-style table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))

    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    sep_line = "-|-".join("-" * w for w in widths)
    data_lines = []
    for row in rows:
        cells = [str(c).ljust(widths[i]) if i < len(widths) else str(c) for i, c in enumerate(row)]
        data_lines.append(" | ".join(cells))

    return f"{header_line}\n{sep_line}\n" + "\n".join(data_lines)


# ── Simulation-Specific Formatters ──────────────────────────────────────────

def format_launch(data: dict) -> str:
    """Format a successful simulation launch."""
    lines = [
        header_box("AgentCiv Simulation", "Civilisation spawned"),
        "",
        kv("Session", data.get("session_id", "?")),
        kv("Agents", data.get("agents", "?")),
        kv("World", f"{data.get('grid_width', '?')}x{data.get('grid_height', '?')}"),
        kv("Ticks", data.get("ticks", "?")),
        kv("Preset", data.get("preset", "custom")),
        "",
    ]
    if data.get("dimensions"):
        lines.append(section("Dimension Overrides"))
        for dim, level in data["dimensions"].items():
            lines.append(kv(f"  {dim}", level))
        lines.append("")

    lines.append(
        whats_next([
            f"Check status: agentciv_sim_status(session_id='{data.get('session_id', '...')}')",
            f"Intervene: agentciv_sim_intervene(session_id='{data.get('session_id', '...')}', action='broadcast', message='...')",
            "Wait for completion, then check emergence metrics",
        ])
    )
    return "\n".join(lines)


def format_status(data: dict) -> str:
    """Format simulation status."""
    lines = [
        header_box("Simulation Status", data.get("state", "unknown")),
        "",
        kv("Session", data.get("session_id", "?")),
        kv("Tick", f"{data.get('current_tick', 0)} / {data.get('target_ticks', '?')}"),
        kv("Alive agents", data.get("alive_agents", "?")),
        kv("State", data.get("state", "unknown")),
    ]

    emergence = data.get("emergence")
    if emergence:
        lines.append(section("Emergence Metrics"))
        lines.append(kv("Composite Score", f"{emergence.get('composite_score', 0):.4f}"))
        lines.append(kv("Innovations", emergence.get("innovation_count", 0)))
        lines.append(kv("Rules", emergence.get("rules_established", 0)))
        lines.append(kv("Bonded Pairs", emergence.get("bonded_pairs", 0)))
        lines.append(kv("Avg Wellbeing", f"{emergence.get('avg_wellbeing', 0):.3f}"))

    milestones = data.get("milestones", [])
    if milestones:
        lines.append(section("Recent Milestones"))
        for m in milestones[-5:]:
            lines.append(f"  [{m.get('tick', '?')}] {m.get('description', '?')}")

    return "\n".join(lines)


def format_configure(data: dict) -> str:
    """Format config preview."""
    lines = [
        header_box("Configuration Preview"),
        "",
    ]
    summary = data.get("summary", "")
    if summary:
        for line in summary.split("\n"):
            lines.append(line)
        lines.append("")

    params = data.get("parameters", {})
    if params:
        lines.append(section("Parameters"))
        for k, v in sorted(params.items()):
            lines.append(kv(f"  {k}", v))

    lines.append("")
    lines.append(
        whats_next([
            "Launch: agentciv_sim_launch(...) with the same settings",
            "Adjust: change dimensions or add --set overrides",
        ])
    )
    return "\n".join(lines)


def format_dimensions(data: dict) -> str:
    """Format dimensions listing."""
    lines = [
        header_box("Tuneable Dimensions"),
        "",
        "Override any dimension when launching a civilisation.",
        "",
    ]
    for dim in data.get("dimensions", []):
        lines.append(f"  {dim['label']} ({dim['name']})")
        lines.append(f"    {dim['description']}")
        lines.append(f"    Levels: {', '.join(dim['levels'])}")
        lines.append("")

    lines.append(section("Feature Toggles"))
    for feat in data.get("features", []):
        lines.append(f"  {feat['label']}: {feat['description']}")
    lines.append("")

    return "\n".join(lines)


def format_presets(data: dict) -> str:
    """Format presets listing."""
    lines = [
        header_box("Available Presets"),
        "",
    ]
    for p in data.get("presets", []):
        lines.append(f"  {p['name']:15s} {p.get('description', '')}")
    lines.append("")
    custom = data.get("custom_configs", [])
    if custom:
        lines.append(section("Your Custom Configs"))
        for name in custom:
            lines.append(f"  {name}")
        lines.append("")
    return "\n".join(lines)


def format_intervene(data: dict) -> str:
    """Format intervention response."""
    lines = [
        header_box("Gardener Intervention"),
        "",
        kv("Action", data.get("action", "?")),
        status(data.get("success", False), data.get("message", "Applied")),
    ]
    return "\n".join(lines)


def format_error(error: str) -> str:
    """Format an error response."""
    return f"✗ Error: {error}"
