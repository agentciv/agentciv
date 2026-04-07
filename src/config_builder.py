"""Civilisation Configuration Builder.

Three layers of customisation for spawning unique AI civilisations:

1. **Dimensions** — high-level knobs (world-size, resources, social-drives, etc.)
   that map to groups of raw parameters. Used by CLI flags and the MCP server.

2. **Interactive Wizard** — walks the user through meaningful choices,
   explains trade-offs, and saves a named custom config.

3. **Raw overrides** — ``--set key=value`` for any SimulationConfig field.
   Power-user escape hatch.

Every layer produces a dict of parameter overrides that gets merged on top of
a base config (preset or default).  Merge order:

    preset defaults → dimension overrides → raw --set overrides
"""

from __future__ import annotations

import copy
import sys
from dataclasses import fields as dc_fields
from pathlib import Path
from typing import Any

import yaml

from src.config import SimulationConfig

# ── Where custom configs live ───────────────────────────────────────────────

USER_CONFIG_DIR = Path.home() / ".agentciv-sim" / "configs"
BUILTIN_PRESETS_DIR = Path(__file__).parent / "presets"


# ── Dimension Definitions ───────────────────────────────────────────────────
# Each dimension is a high-level concept (e.g. "resources") with named levels
# that map to concrete SimulationConfig overrides.

DIMENSIONS: dict[str, dict[str, Any]] = {
    "world_size": {
        "_label": "World Size",
        "_description": "Physical size of the world grid",
        "_flag": "--world-size",
        "tiny":   {"grid_width": 15, "grid_height": 15},
        "small":  {"grid_width": 25, "grid_height": 25},
        "medium": {"grid_width": 40, "grid_height": 40},
        "large":  {"grid_width": 60, "grid_height": 60},
        "huge":   {"grid_width": 80, "grid_height": 80},
    },
    "resources": {
        "_label": "Resource Availability",
        "_description": "How plentiful and fast-regenerating resources are",
        "_flag": "--resources",
        "scarce": {
            "resource_max_per_tile": 0.4,
            "resource_regeneration_rate": 0.02,
            "resource_distribution": "scattered",
            "resource_cluster_count": 2,
        },
        "limited": {
            "resource_max_per_tile": 0.6,
            "resource_regeneration_rate": 0.03,
            "resource_distribution": "scattered",
            "resource_cluster_count": 3,
        },
        "moderate": {
            "resource_max_per_tile": 0.8,
            "resource_regeneration_rate": 0.05,
            "resource_distribution": "clustered",
            "resource_cluster_count": 3,
        },
        "abundant": {
            "resource_max_per_tile": 1.0,
            "resource_regeneration_rate": 0.08,
            "resource_distribution": "clustered",
            "resource_cluster_count": 5,
        },
        "unlimited": {
            "resource_max_per_tile": 1.0,
            "resource_regeneration_rate": 0.15,
            "resource_distribution": "clustered",
            "resource_cluster_count": 6,
        },
    },
    "communication": {
        "_label": "Communication Range",
        "_description": "How far agents can talk to each other",
        "_flag": "--communication",
        "isolated": {"agent_communication_range": 1},
        "limited":  {"agent_communication_range": 2},
        "moderate": {"agent_communication_range": 3},
        "extended": {"agent_communication_range": 5},
        "global":   {"agent_communication_range": 99},
    },
    "social_drives": {
        "_label": "Social Drives",
        "_description": "How strongly agents seek social connection",
        "_flag": "--social-drives",
        "low": {
            "agent_wellbeing_interaction_bonus": 0.02,
            "agent_wellbeing_proximity_bonus": 0.005,
            "agent_bond_threshold": 15,
            "agent_curiosity_social_bonus": 0.01,
        },
        "moderate": {
            "agent_wellbeing_interaction_bonus": 0.05,
            "agent_wellbeing_proximity_bonus": 0.01,
            "agent_bond_threshold": 10,
            "agent_curiosity_social_bonus": 0.02,
        },
        "high": {
            "agent_wellbeing_interaction_bonus": 0.08,
            "agent_wellbeing_proximity_bonus": 0.02,
            "agent_bond_threshold": 5,
            "agent_curiosity_social_bonus": 0.04,
        },
    },
    "curiosity": {
        "_label": "Curiosity",
        "_description": "How driven agents are to explore and discover",
        "_flag": "--curiosity",
        "low": {
            "agent_curiosity_decay_rate": 0.005,
            "agent_curiosity_exploration_bonus": 0.01,
            "agent_curiosity_discovery_bonus": 0.02,
        },
        "moderate": {
            "agent_curiosity_decay_rate": 0.003,
            "agent_curiosity_exploration_bonus": 0.03,
            "agent_curiosity_discovery_bonus": 0.04,
        },
        "high": {
            "agent_curiosity_decay_rate": 0.001,
            "agent_curiosity_exploration_bonus": 0.05,
            "agent_curiosity_discovery_bonus": 0.08,
        },
    },
    "survival_pressure": {
        "_label": "Survival Pressure",
        "_description": "How fast agents' needs deplete (higher = harder to survive)",
        "_flag": "--survival",
        "trivial": {"agent_needs_depletion_rate": 0.005},
        "easy":    {"agent_needs_depletion_rate": 0.01},
        "moderate":{"agent_needs_depletion_rate": 0.02},
        "hard":    {"agent_needs_depletion_rate": 0.04},
        "brutal":  {"agent_needs_depletion_rate": 0.06},
    },
    "reflection": {
        "_label": "Reflection Frequency",
        "_description": "How often agents pause to reflect on their experiences",
        "_flag": "--reflection",
        "rare":       {"agent_reflection_interval": 50},
        "occasional": {"agent_reflection_interval": 25},
        "frequent":   {"agent_reflection_interval": 10},
        "constant":   {"agent_reflection_interval": 5},
    },
}

# Feature toggles — these are simple on/off flags
FEATURE_TOGGLES: dict[str, dict[str, str]] = {
    "innovation":    {"param": "enable_innovation",      "label": "Innovation",       "description": "Agents can invent novel structures"},
    "composition":   {"param": "enable_composition",     "label": "Composition",      "description": "Agents can combine structures"},
    "specialisation":{"param": "enable_specialisation",  "label": "Specialisation",   "description": "Agents develop expertise over time"},
    "governance":    {"param": "enable_collective_rules", "label": "Governance",      "description": "Agents can propose and vote on rules"},
    "coevolution":   {"param": "enable_environmental_coevolution", "label": "Environmental Co-evolution", "description": "World responds to agent activity"},
    "shifts":        {"param": "enable_environmental_shifts",      "label": "Environmental Shifts",       "description": "Periodic environmental disruptions"},
}


# ── Helpers ─────────────────────────────────────────────────────────────────

def dimension_names() -> list[str]:
    return list(DIMENSIONS.keys())


def dimension_levels(dim: str) -> list[str]:
    """Return the valid level names for a dimension."""
    return [k for k in DIMENSIONS.get(dim, {}) if not k.startswith("_")]


def dimension_info(dim: str) -> dict[str, str]:
    """Return label and description for a dimension."""
    d = DIMENSIONS.get(dim, {})
    return {"label": d.get("_label", dim), "description": d.get("_description", "")}


def resolve_dimension(dim: str, level: str) -> dict[str, Any]:
    """Resolve a dimension + level to a dict of config overrides."""
    d = DIMENSIONS.get(dim)
    if d is None:
        raise ValueError(f"Unknown dimension: {dim}. Available: {dimension_names()}")
    overrides = d.get(level)
    if overrides is None:
        levels = dimension_levels(dim)
        raise ValueError(f"Unknown level '{level}' for {dim}. Available: {levels}")
    return dict(overrides)


def resolve_feature_toggle(feature: str, enabled: bool) -> dict[str, Any]:
    """Resolve a feature toggle to a config override."""
    toggle = FEATURE_TOGGLES.get(feature)
    if toggle is None:
        raise ValueError(f"Unknown feature: {feature}. Available: {list(FEATURE_TOGGLES)}")
    return {toggle["param"]: enabled}


def parse_set_value(raw: str) -> Any:
    """Parse a --set value string into its Python type."""
    if raw.lower() in ("true", "yes"):
        return True
    if raw.lower() in ("false", "no"):
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def merge_overrides(base: dict[str, Any], *override_dicts: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple override dicts onto a base config dict."""
    result = dict(base)
    for overrides in override_dicts:
        result.update(overrides)
    return result


def build_config(
    preset: str | None = None,
    dimensions: dict[str, str] | None = None,
    features: dict[str, bool] | None = None,
    agents: int | None = None,
    raw_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete config dict from layered inputs.

    Merge order: preset → dimensions → features → agent count → raw overrides.
    """
    # Layer 0: base from preset or defaults
    if preset:
        path = get_config_path(preset)
        if path and path.exists():
            with open(path) as f:
                base = yaml.safe_load(f) or {}
        else:
            base = {}
    else:
        base = {}

    # Layer 1: dimension overrides
    dim_overrides: dict[str, Any] = {}
    for dim, level in (dimensions or {}).items():
        dim_overrides.update(resolve_dimension(dim, level))

    # Layer 2: feature toggles
    feat_overrides: dict[str, Any] = {}
    for feat, enabled in (features or {}).items():
        feat_overrides.update(resolve_feature_toggle(feat, enabled))

    # Layer 3: agent count
    agent_overrides: dict[str, Any] = {}
    if agents is not None:
        agent_overrides["initial_agent_count"] = agents

    # Layer 4: raw overrides
    raw = raw_overrides or {}

    return merge_overrides(base, dim_overrides, feat_overrides, agent_overrides, raw)


def config_dict_to_yaml(config: dict[str, Any]) -> str:
    """Serialize a config dict to YAML with helpful comments."""
    # Filter out internal keys and complex nested dicts for clean YAML
    clean = {}
    valid_keys = {f.name for f in dc_fields(SimulationConfig)}
    for k, v in config.items():
        if k in valid_keys and not isinstance(v, (dict, list)):
            clean[k] = v
    # Add dicts/lists that are simple enough
    for k, v in config.items():
        if k in valid_keys and isinstance(v, (dict, list)):
            clean[k] = v
    return yaml.dump(clean, default_flow_style=False, sort_keys=False)


def get_config_path(name: str) -> Path | None:
    """Find a config by name — checks user configs first, then built-in presets."""
    # User custom configs
    user_path = USER_CONFIG_DIR / f"{name}.yaml"
    if user_path.exists():
        return user_path
    # Built-in presets
    builtin_path = BUILTIN_PRESETS_DIR / f"{name}.yaml"
    if builtin_path.exists():
        return builtin_path
    return None


def save_custom_config(name: str, config: dict[str, Any], description: str = "") -> Path:
    """Save a config dict as a named custom config."""
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = USER_CONFIG_DIR / f"{name}.yaml"

    lines = []
    if description:
        for line in description.split("\n"):
            lines.append(f"# {line}")
        lines.append("")

    lines.append(config_dict_to_yaml(config))
    path.write_text("\n".join(lines))
    return path


def list_custom_configs() -> list[str]:
    """List user's saved custom configs."""
    if not USER_CONFIG_DIR.exists():
        return []
    return sorted(p.stem for p in USER_CONFIG_DIR.glob("*.yaml"))


def describe_config(config: dict[str, Any]) -> str:
    """Generate a human-readable summary of what a config produces."""
    lines = []
    agents = config.get("initial_agent_count", 50)
    w = config.get("grid_width", 50)
    h = config.get("grid_height", 50)
    lines.append(f"  {agents} agents in a {w}x{h} world")

    # Resources
    regen = config.get("resource_regeneration_rate", 0.05)
    rmax = config.get("resource_max_per_tile", 1.0)
    if regen <= 0.02:
        lines.append("  Resources: scarce (slow regeneration)")
    elif regen >= 0.10:
        lines.append("  Resources: abundant (fast regeneration)")
    else:
        lines.append(f"  Resources: moderate (regen={regen}, max={rmax})")

    # Communication
    comm = config.get("agent_communication_range", 2)
    if comm >= 20:
        lines.append("  Communication: global")
    elif comm >= 5:
        lines.append(f"  Communication: extended (range {comm})")
    elif comm <= 1:
        lines.append("  Communication: isolated (range 1)")
    else:
        lines.append(f"  Communication: range {comm}")

    # Features
    features_on = []
    features_off = []
    for feat, info in FEATURE_TOGGLES.items():
        if config.get(info["param"], True):
            features_on.append(info["label"])
        else:
            features_off.append(info["label"])
    if features_on:
        lines.append(f"  Enabled: {', '.join(features_on)}")
    if features_off:
        lines.append(f"  Disabled: {', '.join(features_off)}")

    return "\n".join(lines)


# ── Interactive Wizard ──────────────────────────────────────────────────────

def _prompt_choice(label: str, options: list[str], descriptions: dict[str, str] | None = None,
                   default: str | None = None) -> str:
    """Prompt the user to pick from a list of options."""
    print(f"\n  {label}")
    if descriptions:
        for i, opt in enumerate(options, 1):
            desc = descriptions.get(opt, "")
            marker = " (default)" if opt == default else ""
            print(f"    {i}. {opt}{marker}  {desc}")
    else:
        for i, opt in enumerate(options, 1):
            marker = " (default)" if opt == default else ""
            print(f"    {i}. {opt}{marker}")

    while True:
        prompt_str = f"  Choice [1-{len(options)}]"
        if default:
            prompt_str += f" (enter for {default})"
        prompt_str += ": "
        raw = input(prompt_str).strip()
        if not raw and default:
            return default
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            # Try matching by name
            if raw.lower() in [o.lower() for o in options]:
                return next(o for o in options if o.lower() == raw.lower())
        print(f"    Please enter 1-{len(options)} or a valid option name.")


def _prompt_int(label: str, default: int, min_val: int = 1, max_val: int = 200) -> int:
    """Prompt for an integer within bounds."""
    while True:
        raw = input(f"  {label} [{default}]: ").strip()
        if not raw:
            return default
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(f"    Please enter {min_val}-{max_val}.")
        except ValueError:
            print(f"    Please enter a number ({min_val}-{max_val}).")


def _prompt_yn(label: str, default: bool = True) -> bool:
    """Prompt yes/no."""
    d = "Y/n" if default else "y/N"
    raw = input(f"  {label} [{d}]: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes", "1", "true")


def _prompt_name(label: str) -> str:
    """Prompt for a config name (alphanumeric + hyphens)."""
    while True:
        raw = input(f"  {label}: ").strip()
        if raw and all(c.isalnum() or c in "-_" for c in raw):
            return raw
        print("    Use letters, numbers, hyphens, or underscores only.")


def run_wizard() -> tuple[str, dict[str, Any]]:
    """Interactive wizard that builds a custom civilisation config.

    Returns (name, config_dict).
    """
    print()
    print("  ╔═══════════════════════════════════════╗")
    print("  ║     Create Your Own Civilisation      ║")
    print("  ╚═══════════════════════════════════════╝")
    print()
    print("  Answer a few questions to design your unique AI society.")
    print("  Press Enter to accept defaults. You can always edit the config later.")

    config: dict[str, Any] = {}

    # 1. Agent count
    agents = _prompt_int("How many agents?", default=12, min_val=2, max_val=100)
    config["initial_agent_count"] = agents

    # 2. World size
    world_descs = {
        "tiny":   "— 15×15, tight quarters",
        "small":  "— 25×25, cosy",
        "medium": "— 40×40, room to roam",
        "large":  "— 60×60, spread out",
        "huge":   "— 80×80, vast wilderness",
    }
    world = _prompt_choice(
        "World size?",
        ["tiny", "small", "medium", "large", "huge"],
        world_descs,
        default="medium",
    )
    config.update(resolve_dimension("world_size", world))

    # 3. Resources
    res_descs = {
        "scarce":   "— hard to find, forces cooperation or conflict",
        "limited":  "— enough to survive, but not comfortably",
        "moderate": "— balanced, the classic starting point",
        "abundant": "— plenty for everyone, what do they do with surplus?",
        "unlimited":"— survival is trivial, focus shifts to higher needs",
    }
    resources = _prompt_choice(
        "Resource availability?",
        ["scarce", "limited", "moderate", "abundant", "unlimited"],
        res_descs,
        default="moderate",
    )
    config.update(resolve_dimension("resources", resources))

    # 4. Communication
    comm_descs = {
        "isolated": "— range 1, agents must be adjacent to talk",
        "limited":  "— range 2, close proximity only",
        "moderate": "— range 3, can chat across a small area",
        "extended": "— range 5, broad communication",
        "global":   "— unlimited range, everyone can hear everyone",
    }
    communication = _prompt_choice(
        "Communication range?",
        ["isolated", "limited", "moderate", "extended", "global"],
        comm_descs,
        default="moderate",
    )
    config.update(resolve_dimension("communication", communication))

    # 5. Social drives
    social_descs = {
        "low":      "— agents are indifferent to others",
        "moderate": "— balanced social needs",
        "high":     "— agents strongly seek connection and bonding",
    }
    social = _prompt_choice(
        "Social drives?",
        ["low", "moderate", "high"],
        social_descs,
        default="moderate",
    )
    config.update(resolve_dimension("social_drives", social))

    # 6. Survival pressure
    surv_descs = {
        "trivial":  "— almost no needs depletion, utopian",
        "easy":     "— gentle, agents rarely struggle",
        "moderate": "— balanced, must gather regularly",
        "hard":     "— aggressive depletion, survival is a challenge",
        "brutal":   "— extreme, every tick counts",
    }
    survival = _prompt_choice(
        "Survival pressure?",
        ["trivial", "easy", "moderate", "hard", "brutal"],
        surv_descs,
        default="moderate",
    )
    config.update(resolve_dimension("survival_pressure", survival))

    # 7. Curiosity
    cur_descs = {
        "low":      "— agents focus on survival, not exploration",
        "moderate": "— balanced curiosity drive",
        "high":     "— agents are driven to explore and discover",
    }
    curiosity = _prompt_choice(
        "Curiosity drive?",
        ["low", "moderate", "high"],
        cur_descs,
        default="moderate",
    )
    config.update(resolve_dimension("curiosity", curiosity))

    # 8. Reflection
    ref_descs = {
        "rare":       "— every 50 ticks, agents barely introspect",
        "occasional": "— every 25 ticks, periodic self-reflection",
        "frequent":   "— every 10 ticks, deep thinkers",
        "constant":   "— every 5 ticks, philosopher-agents (uses more tokens)",
    }
    reflection = _prompt_choice(
        "Reflection frequency?",
        ["rare", "occasional", "frequent", "constant"],
        ref_descs,
        default="occasional",
    )
    config.update(resolve_dimension("reflection", reflection))

    # 9. Features
    print("\n  Which features should be enabled?")
    for feat, info in FEATURE_TOGGLES.items():
        enabled = _prompt_yn(f"  {info['label']}? ({info['description']})", default=True)
        config.update(resolve_feature_toggle(feat, enabled))

    # Preview
    print("\n  ── Your Civilisation ──────────────────────────")
    print(describe_config(config))

    # Name
    print()
    name = _prompt_name("Name this civilisation (e.g. harsh-isolationists)")

    # Description
    desc = input("  Short description (optional): ").strip()

    # Save
    path = save_custom_config(name, config, desc)
    print(f"\n  Saved to {path}")
    print(f"  Run it:  agentciv-sim run --preset {name}")
    print(f"  Edit it: open {path}")
    print()

    return name, config
