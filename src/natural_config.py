"""Natural Language Configuration — describe a civilisation, get a config.

Maps natural language descriptions to dimension overrides using keyword matching.
No LLM required — works offline with pattern matching.

Usage:
    agentciv-sim run --describe "a tiny harsh world with no governance"
    agentciv-sim run --describe "20 curious agents in an abundant paradise"
"""

from __future__ import annotations

import re
from typing import Any

from src.config_builder import (
    DIMENSIONS,
    FEATURE_TOGGLES,
    build_config,
    dimension_levels,
)

# ── Keyword → Dimension Mapping ────────────────────────────────────────────

_KEYWORD_MAP: list[tuple[list[str], str, str]] = [
    # (keywords, dimension, level)

    # World size
    (["tiny", "minuscule", "cramped"], "world_size", "tiny"),
    (["small", "little", "compact", "cosy", "cozy"], "world_size", "small"),
    (["medium", "balanced", "moderate-size", "normal"], "world_size", "medium"),
    (["large", "big", "expansive", "wide", "spacious"], "world_size", "large"),
    (["huge", "vast", "enormous", "massive", "epic"], "world_size", "huge"),

    # Resources
    (["barren", "desolate", "starving", "famine"], "resources", "scarce"),
    (["scarce", "limited resources", "resource-poor", "harsh"], "resources", "scarce"),
    (["moderate resources", "some resources"], "resources", "moderate"),
    (["abundant", "plentiful", "rich", "lush", "fertile"], "resources", "abundant"),
    (["unlimited", "infinite", "paradise", "utopia", "eden"], "resources", "unlimited"),

    # Communication
    (["isolated", "silent", "mute", "no communication", "cannot communicate"], "communication", "isolated"),
    (["limited communication", "quiet"], "communication", "limited"),
    (["telepathic", "omniscient", "global communication", "can all hear"], "communication", "global"),
    (["extended communication", "far-reaching"], "communication", "extended"),

    # Social drives
    (["antisocial", "loner", "solitary", "indifferent"], "social_drives", "low"),
    (["social", "friendly", "gregarious", "bonding", "communal"], "social_drives", "high"),

    # Curiosity
    (["incurious", "passive", "uncurious", "stationary"], "curiosity", "low"),
    (["curious", "explorer", "adventurous", "inquisitive", "wanderer"], "curiosity", "high"),

    # Survival pressure
    (["trivial survival", "post-scarcity", "no danger", "safe"], "survival_pressure", "trivial"),
    (["easy survival", "gentle", "forgiving"], "survival_pressure", "easy"),
    (["harsh", "brutal", "unforgiving", "deadly", "extreme", "hostile", "dangerous"], "survival_pressure", "brutal"),
    (["hard", "difficult", "challenging", "tough"], "survival_pressure", "hard"),

    # Reflection
    (["philosophical", "thoughtful", "contemplative", "introspective", "deep thinkers"], "reflection", "frequent"),
    (["unreflective", "instinctive", "reactive"], "reflection", "rare"),
]

_FEATURE_KEYWORDS: list[tuple[list[str], str, bool]] = [
    # (keywords, feature, enabled)
    (["no innovation", "cannot innovate", "no invention", "primitive"], "innovation", False),
    (["innovative", "creative", "inventive"], "innovation", True),
    (["no governance", "anarchic", "anarchy", "no rules", "lawless"], "governance", False),
    (["governed", "democratic", "rule-based", "orderly"], "governance", True),
    (["no specialisation", "generalist", "jack of all trades"], "specialisation", False),
    (["specialist", "specialised", "expert"], "specialisation", True),
    (["primordial", "nothing enabled", "pure survival"], "innovation", False),
]

_AGENT_COUNT_PATTERNS = [
    (r"(\d+)\s+agents?", lambda m: int(m.group(1))),
    (r"(\d+)\s+\w+\s+agents?", lambda m: int(m.group(1))),  # "20 curious agents"
    (r"(\d+)\s+\w+\s+\w+\s+agents?", lambda m: int(m.group(1))),  # "20 very curious agents"
    (r"(\d+)\s+people", lambda m: int(m.group(1))),
    (r"(\d+)\s+entities", lambda m: int(m.group(1))),
    (r"a?\s*pair", lambda _: 2),
    (r"a?\s*handful", lambda _: 5),
    (r"a?\s*dozen", lambda _: 12),
    (r"many\s+agents?", lambda _: 30),
    (r"few\s+agents?", lambda _: 4),
    (r"lots?\s+of\s+agents?", lambda _: 25),
    (r"crowd", lambda _: 40),
    (r"army", lambda _: 50),
]


def parse_description(text: str) -> dict[str, Any]:
    """Parse a natural language description into config build parameters.

    Returns a dict with keys: dimensions, features, agents, preset.
    """
    lower = text.lower().strip()

    # Check for preset names
    preset = "default"
    from src.config_builder import get_config_path
    for word in lower.split():
        clean = word.strip(".,!?;:'\"")
        if get_config_path(clean):
            preset = clean
            break

    # Extract dimensions
    dimensions: dict[str, str] = {}
    for keywords, dim, level in _KEYWORD_MAP:
        for kw in keywords:
            if kw in lower:
                dimensions[dim] = level
                break

    # Extract features
    features: dict[str, bool] = {}
    for keywords, feat, enabled in _FEATURE_KEYWORDS:
        for kw in keywords:
            if kw in lower:
                features[feat] = enabled
                break

    # Handle "primordial" — disable everything
    if "primordial" in lower or "nothing enabled" in lower:
        for feat in FEATURE_TOGGLES:
            features[feat] = False

    # Extract agent count
    agents = None
    for pattern, extractor in _AGENT_COUNT_PATTERNS:
        m = re.search(pattern, lower)
        if m:
            agents = extractor(m)
            agents = max(2, min(100, agents))
            break

    return {
        "preset": preset,
        "dimensions": dimensions,
        "features": features,
        "agents": agents,
    }


def describe_to_config(text: str) -> dict[str, Any]:
    """Convert a natural language description to a full config dict."""
    parsed = parse_description(text)
    return build_config(
        preset=parsed["preset"],
        dimensions=parsed["dimensions"] if parsed["dimensions"] else None,
        features=parsed["features"] if parsed["features"] else None,
        agents=parsed["agents"],
    )


def describe_to_summary(text: str) -> str:
    """Convert description → config → human-readable summary."""
    from src.config_builder import describe_config
    parsed = parse_description(text)
    config = build_config(
        preset=parsed["preset"],
        dimensions=parsed["dimensions"] if parsed["dimensions"] else None,
        features=parsed["features"] if parsed["features"] else None,
        agents=parsed["agents"],
    )

    lines = [f"  Interpreted: \"{text}\"", ""]

    if parsed["dimensions"]:
        lines.append("  Detected dimensions:")
        for dim, level in parsed["dimensions"].items():
            lines.append(f"    {dim} = {level}")
    if parsed["features"]:
        lines.append("  Detected features:")
        for feat, enabled in parsed["features"].items():
            lines.append(f"    {feat} = {'on' if enabled else 'off'}")
    if parsed["agents"]:
        lines.append(f"  Detected agent count: {parsed['agents']}")
    if parsed["preset"] != "default":
        lines.append(f"  Base preset: {parsed['preset']}")

    lines.append("")
    lines.append("  Result:")
    lines.append(describe_config(config))

    return "\n".join(lines)
