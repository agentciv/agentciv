#!/usr/bin/env python3
"""AgentCiv Simulation — CLI entry point.

Beautiful developer interface for launching AI civilisations.

Usage:
    agentciv-sim run                                    # default preset, 100 ticks
    agentciv-sim run --preset scarce                    # resource scarcity world
    agentciv-sim run --preset utopia -t 200             # utopian world, 200 ticks
    agentciv-sim run --agents 20 --resources abundant   # custom dimensions
    agentciv-sim run --set grid_width=100               # raw parameter override
    agentciv-sim create                                 # interactive wizard
    agentciv-sim create --from scarce                   # wizard starting from preset
    agentciv-sim configs                                # list saved custom configs
    agentciv-sim experiment --presets default,scarce -t 50
    agentciv-sim info                                   # list all presets
    agentciv-sim info scarce                            # details of one preset
    agentciv-sim dimensions                             # list all tuneable dimensions
    agentciv-sim describe --preset scarce --agents 30   # preview a config
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import textwrap
from pathlib import Path

# Ensure the project root is on sys.path so `src.*` imports resolve.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ── Preset Discovery ────────────────────────────────────────────────────────

PRESETS_DIR = Path(__file__).parent / "presets"

_PRESET_DESCRIPTIONS: dict[str, str] = {
    "default": "Balanced starting point — 12 agents, moderate resources, all features",
    "scarce": "Resource scarcity — forces cooperation or competition",
    "abundant": "Resource abundance — do agents still cooperate?",
    "dense": "High population density — 20 agents, small world, forced interaction",
    "sparse": "Low density — 6 agents, large world, isolation pressure",
    "cooperative": "Conditions favouring cooperation — clustered resources, strong social drives",
    "competitive": "Conditions favouring competition — scattered resources, limited communication",
    "innovative": "Maximise innovation — high curiosity, frequent reflection",
    "minimal": "Cheapest possible run — 4 agents, small world, basic features",
    "quick": "Fast validation — 6 agents, smaller world, all features",
    "primordial": "Nothing enabled — no building, no innovation, no governance. Pure survival.",
    "utopia": "Maximum everything — what do agents do when survival is trivial?",
}


def get_preset_path(name: str) -> Path | None:
    """Get the YAML path for a named preset (or custom config)."""
    from src.config_builder import get_config_path
    return get_config_path(name)


def list_presets() -> list[str]:
    """List all available preset names."""
    if not PRESETS_DIR.exists():
        return []
    return sorted(p.stem for p in PRESETS_DIR.glob("*.yaml"))


# ── CLI Commands ────────────────────────────────────────────────────────────

def cmd_run(args: argparse.Namespace) -> None:
    """Run a civilisation simulation."""
    from src.config_builder import (
        build_config,
        config_dict_to_yaml,
        describe_config,
        parse_set_value,
    )

    run_script = _PROJECT_ROOT / "scripts" / "run.py"

    # ── Natural language mode ──
    if args.describe:
        from src.natural_config import parse_description, describe_to_summary
        print()
        print(describe_to_summary(args.describe))
        print()
        parsed = parse_description(args.describe)
        # Merge NL-detected params into the explicit args
        if parsed["agents"] and not args.agents:
            args.agents = parsed["agents"]
        if parsed["preset"] != "default" and not args.preset:
            args.preset = parsed["preset"]
        # Apply NL dimensions as defaults (explicit flags override)
        nl_dims = parsed.get("dimensions", {})
        nl_feats = parsed.get("features", {})
    else:
        nl_dims = {}
        nl_feats = {}

    # ── Build merged config ──
    # Collect dimension overrides from CLI flags
    dimensions: dict[str, str] = dict(nl_dims)  # NL defaults first
    for dim_name in ("world_size", "resources", "communication", "social_drives",
                     "curiosity", "survival_pressure", "reflection"):
        cli_attr = dim_name.replace("-", "_")
        val = getattr(args, cli_attr, None)
        if val:
            dimensions[dim_name] = val

    # Collect feature toggles (NL defaults, then explicit flags override)
    features: dict[str, bool] = dict(nl_feats)
    for feat in ("innovation", "composition", "specialisation", "governance",
                 "coevolution", "shifts"):
        enable_attr = f"enable_{feat}"
        disable_attr = f"no_{feat}"
        if getattr(args, enable_attr, False):
            features[feat] = True
        elif getattr(args, disable_attr, False):
            features[feat] = False

    # Collect --set overrides
    raw_overrides: dict[str, any] = {}
    for s in (args.set or []):
        if "=" not in s:
            _error(f"Invalid --set format: {s} (expected key=value)")
            sys.exit(1)
        key, val = s.split("=", 1)
        raw_overrides[key.strip()] = parse_set_value(val.strip())

    has_custom = dimensions or features or args.agents or raw_overrides

    if has_custom or not args.preset:
        # Build merged config
        config = build_config(
            preset=args.preset or "default",
            dimensions=dimensions if dimensions else None,
            features=features if features else None,
            agents=args.agents,
            raw_overrides=raw_overrides if raw_overrides else None,
        )

        # Write temp YAML for run.py
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", prefix="agentciv_",
            dir=str(_PROJECT_ROOT), delete=False,
        )
        tmp.write(config_dict_to_yaml(config))
        tmp.close()
        config_path = tmp.name
    else:
        # Pure preset — pass directly
        preset_path = get_preset_path(args.preset)
        if preset_path is None:
            _error(f"Unknown preset: {args.preset}")
            _error(f"Available: {', '.join(list_presets())}")
            sys.exit(1)
        config_path = str(preset_path)
        config = None

    # Build run.py command
    cmd_args = [sys.executable, str(run_script)]
    cmd_args.extend(["--config", config_path])

    ticks = args.ticks or 100
    cmd_args.extend(["--ticks", str(ticks)])

    if not args.realtime:
        cmd_args.append("--fast")

    cmd_args.append("--metrics")

    if args.output:
        cmd_args.extend(["--output", args.output])

    if args.record:
        cmd_args.append("--record")

    if args.api:
        cmd_args.append("--api")
        if args.api_port:
            cmd_args.extend(["--api-port", str(args.api_port)])

    if args.preset:
        cmd_args.extend(["--preset", args.preset])
    if args.run_id:
        cmd_args.extend(["--run-id", args.run_id])

    if args.gardener:
        cmd_args.append("--gardener")

    # Print header
    _print_run_header(args, config)

    # Execute
    os.execv(sys.executable, cmd_args)


def cmd_create(args: argparse.Namespace) -> None:
    """Interactive wizard to create a custom civilisation config."""
    from src.config_builder import run_wizard

    _header()
    run_wizard()


def cmd_describe(args: argparse.Namespace) -> None:
    """Preview what a config would produce without running it."""
    from src.config_builder import (
        build_config,
        describe_config,
        parse_set_value,
    )

    # Natural language mode
    if getattr(args, "natural", ""):
        from src.natural_config import describe_to_summary
        _header()
        print(describe_to_summary(args.natural))
        print()
        return

    dimensions: dict[str, str] = {}
    for dim_name in ("world_size", "resources", "communication", "social_drives",
                     "curiosity", "survival_pressure", "reflection"):
        val = getattr(args, dim_name.replace("-", "_"), None)
        if val:
            dimensions[dim_name] = val

    features: dict[str, bool] = {}
    for feat in ("innovation", "composition", "specialisation", "governance",
                 "coevolution", "shifts"):
        if getattr(args, f"enable_{feat}", False):
            features[feat] = True
        elif getattr(args, f"no_{feat}", False):
            features[feat] = False

    raw_overrides: dict[str, any] = {}
    for s in (args.set or []):
        if "=" in s:
            key, val = s.split("=", 1)
            raw_overrides[key.strip()] = parse_set_value(val.strip())

    config = build_config(
        preset=args.preset or "default",
        dimensions=dimensions if dimensions else None,
        features=features if features else None,
        agents=args.agents,
        raw_overrides=raw_overrides if raw_overrides else None,
    )

    _header()
    print("  Configuration Preview:")
    print()
    print(describe_config(config))
    print()
    print("  Full parameters:")
    for k, v in sorted(config.items()):
        print(f"    {k}: {v}")
    print()
    print("  To run this:")
    parts = ["agentciv-sim run"]
    if args.preset:
        parts.append(f"--preset {args.preset}")
    for dim, level in dimensions.items():
        flag = dim.replace("_", "-")
        parts.append(f"--{flag} {level}")
    if args.agents:
        parts.append(f"--agents {args.agents}")
    print(f"    {' '.join(parts)}")
    print()


def cmd_configs(args: argparse.Namespace) -> None:
    """List user's saved custom configs."""
    from src.config_builder import list_custom_configs, USER_CONFIG_DIR

    _header()
    custom = list_custom_configs()

    print("  Built-in presets:")
    print()
    for name in list_presets():
        desc = _PRESET_DESCRIPTIONS.get(name, "")
        print(f"    {name:15s} {desc}")

    print()
    if custom:
        print(f"  Your custom configs ({USER_CONFIG_DIR}):")
        print()
        for name in custom:
            print(f"    {name}")
    else:
        print("  No custom configs yet. Create one with:")
        print("    agentciv-sim create")
    print()


def cmd_dimensions(args: argparse.Namespace) -> None:
    """List all tuneable dimensions and their levels."""
    from src.config_builder import DIMENSIONS, FEATURE_TOGGLES, dimension_levels

    _header()
    print("  Tuneable Dimensions")
    print("  Override any dimension on the run command:")
    print("    agentciv-sim run --resources scarce --world-size large --agents 20")
    print()

    for dim_name, dim_data in DIMENSIONS.items():
        label = dim_data.get("_label", dim_name)
        desc = dim_data.get("_description", "")
        flag = dim_data.get("_flag", f"--{dim_name}")
        levels = dimension_levels(dim_name)
        print(f"  {label} ({flag})")
        if desc:
            print(f"    {desc}")
        print(f"    Levels: {', '.join(levels)}")
        print()

    print("  Feature Toggles")
    print("    Enable:  --enable-innovation")
    print("    Disable: --no-innovation")
    print()
    for feat, info in FEATURE_TOGGLES.items():
        print(f"    {info['label']:30s} {info['description']}")
    print()

    print("  Raw Parameter Override (--set)")
    print("    Any SimulationConfig field:  --set grid_width=100 --set llm_temperature=0.9")
    print()


def cmd_experiment(args: argparse.Namespace) -> None:
    """Run a comparative experiment across multiple presets."""
    import subprocess
    import time

    presets = [p.strip() for p in args.presets.split(",")]
    ticks = args.ticks or 50
    runs = args.runs or 1

    for p in presets:
        if get_preset_path(p) is None:
            _error(f"Unknown preset: {p}")
            _error(f"Available: {', '.join(list_presets())}")
            sys.exit(1)

    total_runs = len(presets) * runs
    _header()
    print(f"  Experiment: {len(presets)} presets x {runs} runs = {total_runs} total")
    print(f"  Presets: {', '.join(presets)}")
    print(f"  Ticks per run: {ticks}")
    print()

    results_dir = Path(args.output_dir) if args.output_dir else Path("./experiment_results")
    results_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    run_num = 0

    for preset in presets:
        for rep in range(runs):
            run_num += 1
            run_id = f"{preset}_r{rep}"
            output_path = results_dir / f"{run_id}.json"

            print(f"  [{run_num}/{total_runs}] Running {preset} (run {rep + 1}/{runs})...")

            preset_path = get_preset_path(preset)
            cmd = [
                sys.executable,
                str(_PROJECT_ROOT / "scripts" / "run.py"),
                "--config", str(preset_path),
                "--ticks", str(ticks),
                "--fast",
                "--output", str(output_path),
                "--preset", preset,
                "--run-id", run_id,
            ]

            start = time.time()
            result = subprocess.run(cmd, cwd=str(_PROJECT_ROOT), capture_output=True, text=True)
            elapsed = time.time() - start

            if result.returncode == 0 and output_path.exists():
                data = json.loads(output_path.read_text())
                emergence = data.get("emergence", {})
                score = emergence.get("composite_score", 0)
                innovations = emergence.get("innovation_count", 0)
                rules = emergence.get("rules_established", 0)
                all_results.append({
                    "preset": preset,
                    "run": rep,
                    "score": score,
                    "innovations": innovations,
                    "rules": rules,
                    "time": round(elapsed, 1),
                })
                print(f"           Score: {score:.4f} | Innovations: {innovations} | "
                      f"Rules: {rules} | Time: {elapsed:.0f}s")
            else:
                all_results.append({
                    "preset": preset,
                    "run": rep,
                    "score": 0,
                    "error": result.stderr[:200] if result.stderr else "unknown",
                })
                print(f"           FAILED: {result.stderr[:100] if result.stderr else 'unknown error'}")

    print()
    _print_comparison(all_results, presets)

    summary_path = results_dir / "experiment_summary.json"
    summary_path.write_text(json.dumps({
        "presets": presets,
        "ticks": ticks,
        "runs_per_preset": runs,
        "results": all_results,
    }, indent=2))
    print(f"\n  Results saved to {results_dir}/")


def cmd_info(args: argparse.Namespace) -> None:
    """Show preset information."""
    import yaml
    from src.config_builder import describe_config

    if args.preset_name:
        name = args.preset_name
        path = get_preset_path(name)
        if path is None:
            _error(f"Unknown preset: {name}")
            sys.exit(1)

        desc = _PRESET_DESCRIPTIONS.get(name, "")
        config = yaml.safe_load(path.read_text()) or {}

        _header()
        print(f"  Preset: {name}")
        if desc:
            print(f"  {desc}")
        print()
        print(describe_config(config))
        print()
        print("  Raw configuration:")
        for key, value in sorted(config.items()):
            print(f"    {key}: {value}")
        print()
        print(f"  Run it:  agentciv-sim run --preset {name}")
        print(f"  Customise:  agentciv-sim run --preset {name} --agents 20 --resources abundant")
        print()
    else:
        _header()
        print("  Available presets:\n")
        for name in list_presets():
            desc = _PRESET_DESCRIPTIONS.get(name, "")
            print(f"    {name:15s} {desc}")
        print()
        print("  Custom configs:")
        from src.config_builder import list_custom_configs
        custom = list_custom_configs()
        if custom:
            for name in custom:
                print(f"    {name:15s} (custom)")
        else:
            print("    None yet — create one with: agentciv-sim create")
        print()
        print("  Quick start:")
        print("    agentciv-sim run                              # default, 100 ticks")
        print("    agentciv-sim run --preset scarce -t 50        # named preset")
        print("    agentciv-sim run --agents 20 --resources abundant  # dimension overrides")
        print("    agentciv-sim create                           # interactive wizard")
        print("    agentciv-sim dimensions                       # see all tuneable knobs")
        print()


# ── Display Helpers ─────────────────────────────────────────────────────────

def _header() -> None:
    print()
    print("  ╔═══════════════════════════════════════╗")
    print("  ║      AgentCiv Simulation  v0.2.0      ║")
    print("  ║   AI civilisations. Emergent society.  ║")
    print("  ╚═══════════════════════════════════════╝")
    print()


def _print_run_header(args: argparse.Namespace, config: dict | None = None) -> None:
    from src.config_builder import describe_config

    _header()
    preset = args.preset or "default"
    ticks = args.ticks or 100
    desc = _PRESET_DESCRIPTIONS.get(preset, "")

    print(f"  Preset:  {preset}")
    if desc:
        print(f"  {desc}")

    # Show any dimension overrides
    overrides = []
    for dim in ("world_size", "resources", "communication", "social_drives",
                "curiosity", "survival_pressure", "reflection"):
        val = getattr(args, dim, None)
        if val:
            overrides.append(f"{dim}={val}")
    if args.agents:
        overrides.append(f"agents={args.agents}")
    if overrides:
        print(f"  Overrides: {', '.join(overrides)}")

    print(f"  Ticks:   {ticks}")

    if config:
        print()
        print(describe_config(config))

    if args.output:
        print(f"  Output:  {args.output}")
    if args.gardener:
        print("  Mode:    Gardener (mid-run intervention enabled)")
    print()


def _print_comparison(results: list[dict], presets: list[str]) -> None:
    """Print a comparison table of experiment results."""
    from collections import defaultdict

    by_preset: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_preset[r["preset"]].append(r)

    print("  ┌─────────────────┬──────────┬──────────────┬───────────┐")
    print("  │ Preset          │ Score    │ Innovations  │ Rules     │")
    print("  ├─────────────────┼──────────┼──────────────┼───────────┤")

    ranked = []
    for preset in presets:
        runs = by_preset.get(preset, [])
        scores = [r["score"] for r in runs if "error" not in r]
        innovations = [r["innovations"] for r in runs if "error" not in r]
        rules = [r["rules"] for r in runs if "error" not in r]

        if scores:
            avg_score = sum(scores) / len(scores)
            avg_innov = sum(innovations) / len(innovations)
            avg_rules = sum(rules) / len(rules)
            ranked.append((preset, avg_score, avg_innov, avg_rules))
        else:
            ranked.append((preset, 0, 0, 0))

    ranked.sort(key=lambda x: x[1], reverse=True)

    for preset, score, innov, rules in ranked:
        print(f"  │ {preset:15s} │ {score:8.4f} │ {innov:12.1f} │ {rules:9.1f} │")

    print("  └─────────────────┴──────────┴──────────────┴───────────┘")

    if ranked:
        winner = ranked[0]
        print(f"\n  Winner: {winner[0]} (emergence score: {winner[1]:.4f})")


def _error(msg: str) -> None:
    print(f"  Error: {msg}", file=sys.stderr)


# ── Dimension / Feature Flag Helpers ────────────────────────────────────────

def _add_dimension_args(parser: argparse.ArgumentParser) -> None:
    """Add all dimension and feature toggle flags to a parser."""
    dim_group = parser.add_argument_group("civilisation dimensions")

    dim_group.add_argument(
        "--world-size", dest="world_size",
        choices=["tiny", "small", "medium", "large", "huge"],
        help="World grid size (tiny=15x15, small=25x25, medium=40x40, large=60x60, huge=80x80)",
    )
    dim_group.add_argument(
        "--resources",
        choices=["scarce", "limited", "moderate", "abundant", "unlimited"],
        help="Resource availability (scarce → unlimited)",
    )
    dim_group.add_argument(
        "--communication",
        choices=["isolated", "limited", "moderate", "extended", "global"],
        help="Agent communication range",
    )
    dim_group.add_argument(
        "--social-drives", dest="social_drives",
        choices=["low", "moderate", "high"],
        help="How strongly agents seek social connection",
    )
    dim_group.add_argument(
        "--curiosity",
        choices=["low", "moderate", "high"],
        help="How driven agents are to explore and discover",
    )
    dim_group.add_argument(
        "--survival", dest="survival_pressure",
        choices=["trivial", "easy", "moderate", "hard", "brutal"],
        help="Survival difficulty (trivial → brutal)",
    )
    dim_group.add_argument(
        "--reflection",
        choices=["rare", "occasional", "frequent", "constant"],
        help="How often agents reflect on their experiences",
    )
    dim_group.add_argument(
        "--agents", "-a", type=int,
        help="Number of agents (2-100)",
    )

    feat_group = parser.add_argument_group("feature toggles")
    for feat in ("innovation", "composition", "specialisation", "governance",
                 "coevolution", "shifts"):
        feat_group.add_argument(
            f"--enable-{feat}", dest=f"enable_{feat}",
            action="store_true", default=False,
            help=f"Force-enable {feat}",
        )
        feat_group.add_argument(
            f"--no-{feat}", dest=f"no_{feat}",
            action="store_true", default=False,
            help=f"Disable {feat}",
        )

    parser.add_argument(
        "--set", action="append", metavar="KEY=VALUE",
        help="Raw parameter override (e.g. --set grid_width=100). Repeatable.",
    )


# ── Argument Parsing ────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentciv-sim",
        description="AgentCiv Simulation — launch AI civilisations and watch society emerge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            quick start:
              agentciv-sim run                                    # default, 100 ticks
              agentciv-sim run --preset scarce -t 50              # named preset
              agentciv-sim run --agents 20 --resources abundant   # dimension overrides
              agentciv-sim run --preset default --no-governance   # toggle features
              agentciv-sim run --set grid_width=100               # raw parameter
              agentciv-sim create                                 # interactive wizard
              agentciv-sim dimensions                             # see all knobs
              agentciv-sim describe --resources scarce --agents 30  # preview config

            presets:
              default      Balanced starting point (12 agents)
              scarce       Resource scarcity — forces cooperation or competition
              abundant     Resource abundance — do agents still cooperate?
              cooperative  Conditions favouring cooperation
              competitive  Conditions favouring competition
              innovative   Maximise innovation potential
              dense        High population density (20 agents, small world)
              sparse       Low density (6 agents, large world)
              utopia       Maximum everything — what happens when survival is trivial?
              primordial   Nothing enabled — pure survival
              minimal      Cheapest possible run (4 agents)
              quick        Fast validation run (6 agents)

            customisation layers (composable):
              1. Presets       --preset scarce (start from a named base)
              2. Dimensions    --resources abundant --world-size large (override by concept)
              3. Features      --no-governance --enable-innovation (toggle on/off)
              4. Raw params    --set grid_width=100 (any SimulationConfig field)

            examples:
              agentciv-sim run --preset cooperative --ticks 100
              agentciv-sim run --preset utopia -t 200 --output results.json
              agentciv-sim run --agents 4 --resources scarce --no-governance --survival brutal
              agentciv-sim experiment --presets default,scarce,abundant -t 50 --runs 3
              agentciv-sim info scarce
        """),
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # ── run ──
    run_parser = subparsers.add_parser(
        "run", help="Launch a civilisation simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    run_parser.add_argument("--preset", "-p", help="Base preset (default, scarce, abundant, ...)")
    run_parser.add_argument("--config", "-c", help="Custom YAML config file (overrides preset)")
    run_parser.add_argument("--ticks", "-t", type=int, help="Number of ticks (default: 100)")
    run_parser.add_argument("--output", "-o", help="Export run record to JSON file")
    run_parser.add_argument("--record", action="store_true", help="Save per-tick snapshots for replay")
    run_parser.add_argument("--realtime", action="store_true", help="Run in real-time (not fast mode)")
    run_parser.add_argument("--api", action="store_true", help="Start API server for live viewing")
    run_parser.add_argument("--api-port", type=int, help="API server port (default: 8000)")
    run_parser.add_argument("--run-id", help="Unique run identifier")
    run_parser.add_argument("--gardener", action="store_true", help="Enable mid-run intervention mode")
    run_parser.add_argument(
        "--describe", type=str, default="",
        help="Natural language: describe the civilisation you want (e.g. \"20 curious agents in a harsh world\")",
    )
    _add_dimension_args(run_parser)

    # ── create ──
    create_parser = subparsers.add_parser(
        "create", help="Interactive wizard — design your own civilisation",
    )
    create_parser.add_argument("--from", dest="from_preset", help="Start from an existing preset")

    # ── describe ──
    desc_parser = subparsers.add_parser(
        "describe", help="Preview a config without running it",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    desc_parser.add_argument("--preset", "-p", help="Base preset")
    desc_parser.add_argument(
        "--natural", type=str, default="",
        help="Natural language description (e.g. \"harsh world with curious loners\")",
    )
    _add_dimension_args(desc_parser)

    # ── configs ──
    subparsers.add_parser("configs", help="List all presets and saved custom configs")

    # ── dimensions ──
    subparsers.add_parser("dimensions", help="List all tuneable dimensions and feature toggles")

    # ── experiment ──
    exp_parser = subparsers.add_parser("experiment", help="Compare multiple presets")
    exp_parser.add_argument("--presets", required=True, help="Comma-separated preset names")
    exp_parser.add_argument("--ticks", "-t", type=int, help="Ticks per run (default: 50)")
    exp_parser.add_argument("--runs", "-r", type=int, help="Runs per preset (default: 1)")
    exp_parser.add_argument("--output-dir", "-o", help="Directory for results (default: ./experiment_results)")

    # ── info ──
    info_parser = subparsers.add_parser("info", help="Show preset information")
    info_parser.add_argument("preset_name", nargs="?", help="Preset to show details for")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "run": cmd_run,
        "create": cmd_create,
        "describe": cmd_describe,
        "configs": cmd_configs,
        "dimensions": cmd_dimensions,
        "experiment": cmd_experiment,
        "info": cmd_info,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
