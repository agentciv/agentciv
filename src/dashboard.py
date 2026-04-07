"""Rich Terminal Dashboard — beautiful real-time civilisation monitoring.

Replaces plain-text output with a live-updating Rich layout showing:
- Tick progress + elapsed time
- Agent status (count, wellbeing, needs)
- Resource overview
- Chronicler commentary (scrolling, Attenborough-style)
- Milestones timeline
- Recent events (innovations, rules, compositions)
- Emergence metrics (live-updating composite score)

Usage:
    dashboard = Dashboard(config, total_ticks=100)
    dashboard.start()
    # Each tick:
    dashboard.update_tick(tick, tick_report)
    dashboard.add_commentary("First contact. Two agents just discovered they're not alone.")
    dashboard.add_milestone("First Structure", tick=12)
    dashboard.add_event("Agent 3 innovated: Water Filter", style="yellow")
    # End:
    dashboard.stop()
    dashboard.print_story(story_text)
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.padding import Padding
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


console = Console()


class Dashboard:
    """Live-updating Rich terminal dashboard for civilisation simulations."""

    def __init__(
        self,
        config: Any = None,
        total_ticks: int = 100,
        preset: str = "default",
    ) -> None:
        self.config = config
        self.total_ticks = total_ticks
        self.preset = preset
        self.start_time = time.time()

        # State
        self.current_tick = 0
        self.agent_count = 0
        self.avg_wellbeing = 0.0
        self.critical_agents = 0
        self.structure_count = 0
        self.innovation_count = 0
        self.rule_count = 0
        self.bond_count = 0
        self.message_count = 0
        self.composite_score = 0.0
        self.resources: dict[str, float] = {}

        # Scrolling buffers
        self._commentary: deque[str] = deque(maxlen=8)
        self._milestones: deque[str] = deque(maxlen=10)
        self._events: deque[tuple[str, str]] = deque(maxlen=12)  # (text, style)

        # Rich components
        self._progress = Progress(
            SpinnerColumn("dots"),
            TextColumn("[bold cyan]Tick {task.completed}/{task.total}"),
            BarColumn(bar_width=30, complete_style="cyan", finished_style="green"),
            TextColumn("[dim]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        )
        self._task_id = self._progress.add_task("simulation", total=total_ticks)

        self._live: Live | None = None

    def start(self) -> None:
        """Start the live dashboard."""
        self._live = Live(
            self._build_layout(),
            console=console,
            refresh_per_second=4,
            screen=False,
        )
        self._live.start()

    def stop(self) -> None:
        """Stop the live dashboard."""
        if self._live:
            self._live.stop()
            self._live = None

    def update_tick(self, tick: int, tick_report: dict | None = None) -> None:
        """Update dashboard state from a tick report."""
        self.current_tick = tick
        self._progress.update(self._task_id, completed=tick)

        if tick_report:
            pop = tick_report.get("population", {})
            self.agent_count = pop.get("total", self.agent_count)
            self.avg_wellbeing = pop.get("avg_wellbeing", self.avg_wellbeing)
            self.critical_agents = pop.get("agents_with_critical_needs", 0)

            structs = tick_report.get("structures", {})
            self.structure_count = structs.get("total", self.structure_count)

            res = tick_report.get("resources", {})
            if "total_available" in res:
                self.resources = res["total_available"]

            comms = tick_report.get("communication", {})
            self.message_count += comms.get("messages_sent", 0)

            innov = tick_report.get("innovation", {})
            self.innovation_count += innov.get("succeeded", 0)

            rules = tick_report.get("rules", {})
            self.rule_count = rules.get("established_count", self.rule_count)

        if self._live:
            self._live.update(self._build_layout())

    def add_commentary(self, text: str) -> None:
        """Add chronicler commentary."""
        self._commentary.append(text)
        if self._live:
            self._live.update(self._build_layout())

    def add_milestone(self, name: str, tick: int = 0) -> None:
        """Add a milestone to the timeline."""
        self._milestones.append(f"[bold]{tick:>4d}[/bold]  {name}")
        if self._live:
            self._live.update(self._build_layout())

    def add_event(self, text: str, style: str = "dim") -> None:
        """Add an event to the scrolling feed."""
        self._events.append((text, style))
        if self._live:
            self._live.update(self._build_layout())

    def set_emergence(self, score: float) -> None:
        """Update the live emergence score."""
        self.composite_score = score

    # ── Layout Builder ──────────────────────────────────────────────────

    def _build_layout(self) -> Group:
        """Build the complete dashboard layout."""
        return Group(
            self._header_panel(),
            self._progress,
            Text(""),
            self._status_panels(),
            Text(""),
            self._chronicler_panel(),
            self._bottom_panels(),
        )

    def _header_panel(self) -> Panel:
        """Header with title and basic stats."""
        elapsed = time.time() - self.start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)

        grid = Table.grid(padding=(0, 3))
        grid.add_column(justify="left")
        grid.add_column(justify="center")
        grid.add_column(justify="right")

        grid.add_row(
            f"[bold cyan]AgentCiv Simulation[/]",
            f"[dim]Preset: {self.preset}[/]",
            f"[dim]{mins:02d}:{secs:02d} elapsed[/]",
        )

        return Panel(
            grid,
            border_style="cyan",
            padding=(0, 1),
        )

    def _status_panels(self) -> Table:
        """Side-by-side status panels: agents, resources, emergence."""
        grid = Table.grid(padding=(0, 1))
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)

        # Agents panel
        agent_table = Table.grid(padding=(0, 1))
        agent_table.add_column(justify="left")
        agent_table.add_column(justify="right")

        wb_color = "green" if self.avg_wellbeing > 0.6 else "yellow" if self.avg_wellbeing > 0.3 else "red"
        agent_table.add_row("Agents", f"[bold]{self.agent_count}[/]")
        agent_table.add_row("Wellbeing", f"[{wb_color}]{self.avg_wellbeing:.2f}[/]")
        agent_table.add_row("Critical", f"[{'red' if self.critical_agents > 0 else 'green'}]{self.critical_agents}[/]")
        agent_table.add_row("Messages", f"[dim]{self.message_count}[/]")

        agents_panel = Panel(
            agent_table,
            title="[bold]Agents[/]",
            border_style="blue",
            padding=(0, 1),
        )

        # Structures panel
        struct_table = Table.grid(padding=(0, 1))
        struct_table.add_column(justify="left")
        struct_table.add_column(justify="right")

        struct_table.add_row("Structures", f"[bold]{self.structure_count}[/]")
        struct_table.add_row("Innovations", f"[yellow]{self.innovation_count}[/]")
        struct_table.add_row("Rules", f"[magenta]{self.rule_count}[/]")

        structs_panel = Panel(
            struct_table,
            title="[bold]Civilisation[/]",
            border_style="yellow",
            padding=(0, 1),
        )

        # Emergence panel
        emergence_table = Table.grid(padding=(0, 1))
        emergence_table.add_column(justify="left")
        emergence_table.add_column(justify="right")

        score_color = "green" if self.composite_score > 0.5 else "yellow" if self.composite_score > 0.2 else "dim"
        emergence_table.add_row("Score", f"[{score_color} bold]{self.composite_score:.4f}[/]")

        # Resource bars
        for rtype, amount in list(self.resources.items())[:3]:
            bar_len = int(amount * 10)
            bar = "[green]" + "█" * bar_len + "[/]" + "[dim]" + "░" * (10 - bar_len) + "[/]"
            emergence_table.add_row(rtype[:8], bar)

        emergence_panel = Panel(
            emergence_table,
            title="[bold]Emergence[/]",
            border_style="green",
            padding=(0, 1),
        )

        grid.add_row(agents_panel, structs_panel, emergence_panel)
        return grid

    def _chronicler_panel(self) -> Panel:
        """Scrolling chronicler commentary."""
        if not self._commentary:
            content = Text("[dim]Watching...[/]", style="dim italic")
        else:
            lines = []
            for c in self._commentary:
                lines.append(Text(f"  ❖ {c}", style="cyan"))
            content = Group(*lines)

        return Panel(
            content,
            title="[bold cyan]Chronicler[/]",
            subtitle="[dim]David Attenborough mode[/]",
            border_style="cyan",
            padding=(0, 1),
        )

    def _bottom_panels(self) -> Table:
        """Side-by-side: milestones + events feed."""
        grid = Table.grid(padding=(0, 1))
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)

        # Milestones
        if self._milestones:
            milestone_lines = []
            for m in self._milestones:
                milestone_lines.append(Text.from_markup(f"  {m}"))
            milestone_content = Group(*milestone_lines)
        else:
            milestone_content = Text("  Waiting for first milestone...", style="dim italic")

        milestones_panel = Panel(
            milestone_content,
            title="[bold]Milestones[/]",
            border_style="magenta",
            padding=(0, 1),
        )

        # Events feed
        if self._events:
            event_lines = []
            for text, style in list(self._events)[-8:]:
                event_lines.append(Text(f"  {text}", style=style))
            event_content = Group(*event_lines)
        else:
            event_content = Text("  Waiting for events...", style="dim italic")

        events_panel = Panel(
            event_content,
            title="[bold]Events[/]",
            border_style="dim",
            padding=(0, 1),
        )

        grid.add_row(milestones_panel, events_panel)
        return grid

    # ── Post-Run Display ────────────────────────────────────────────────

    def print_story(self, story: str) -> None:
        """Print the end-of-run story beautifully."""
        console.print()
        console.print(Rule("[bold cyan]The Story of This Civilisation[/]", style="cyan"))
        console.print()
        for line in story.strip().split("\n"):
            console.print(f"  {line}")
        console.print()
        console.print(Rule(style="cyan"))
        console.print(
            f"  [dim]Chronicler made {len(self._commentary)} observations. "
            f"{len(self._milestones)} milestones reached.[/]"
        )
        console.print()

    def print_interview(self, agent_id: int, interview: str) -> None:
        """Print an agent interview beautifully."""
        console.print()
        console.print(Rule(f"[bold]Agent {agent_id} — Interview[/]", style="blue"))
        console.print()
        for line in interview.strip().split("\n"):
            console.print(f"  {line}")
        console.print()
        console.print(Rule(style="blue"))
        console.print()

    def print_emergence(self, emergence: Any) -> None:
        """Print final emergence metrics as a Rich table."""
        table = Table(title="Emergence Metrics", border_style="green", padding=(0, 1))
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Composite Score", f"[bold green]{emergence.composite_score:.4f}[/]")
        table.add_row("Innovations", str(emergence.innovation_count))
        table.add_row("Structures", f"{emergence.structure_count} ({emergence.unique_structure_types} types)")
        table.add_row("Relationships", f"{emergence.relationship_count} ({emergence.bonded_pairs} bonded)")
        table.add_row("Rules", f"{emergence.rules_proposed} proposed, {emergence.rules_established} established")
        table.add_row("Avg Wellbeing", f"{emergence.avg_wellbeing:.3f}")
        table.add_row("Avg Maslow Level", f"{emergence.avg_maslow_level:.2f}")
        table.add_row("Specialisations", f"{emergence.total_specialisations} ({emergence.agents_with_specialisation} agents)")
        table.add_row("Messages", str(emergence.total_messages))
        table.add_row("Cooperation Events", str(emergence.cooperation_events))

        console.print()
        console.print(table)
        console.print()


# ── Event Bus Subscriber Factory ────────────────────────────────────────────

def make_dashboard_subscriber(
    dashboard: Dashboard,
    config: Any = None,
) -> callable:
    """Create an event bus subscriber that feeds the dashboard.

    Replaces the plain-text CLI subscriber with Rich dashboard updates.
    """
    log_level = getattr(config, "log_level", "INFO").upper() if config else "INFO"

    async def handle(event: Any) -> None:
        from src.types import BusEventType

        if event.type == BusEventType.TICK_START:
            pass  # Dashboard updates on tick report

        elif event.type == BusEventType.WATCHER_TICK_REPORT:
            dashboard.update_tick(event.tick, event.data)

        elif event.type == BusEventType.WATCHER_NARRATIVE:
            text = event.data.get("text", "")
            source = event.data.get("source", "")
            if text and source == "chronicler":
                dashboard.add_commentary(text)

        elif event.type == BusEventType.WATCHER_MILESTONE:
            name = event.data.get("name", "")
            if name:
                dashboard.add_milestone(name, event.tick)

        elif event.type == BusEventType.INNOVATION_SUCCEEDED:
            name = event.data.get("name", "?")
            dashboard.add_event(f"Agent {event.agent_id} innovated: {name}", "yellow")

        elif event.type == BusEventType.COMPOSITION_DISCOVERED:
            output = event.data.get("output_name", "?")
            inputs = event.data.get("inputs", [])
            dashboard.add_event(f"Composition: {' + '.join(inputs)} → {output}", "yellow")

        elif event.type == BusEventType.RULE_PROPOSED:
            text = event.data.get("text", "?")[:60]
            dashboard.add_event(f"Rule proposed: \"{text}\"", "magenta")

        elif event.type == BusEventType.RULE_ESTABLISHED:
            text = event.data.get("text", "?")[:60]
            dashboard.add_event(f"Rule established: \"{text}\"", "green bold")

        elif event.type == BusEventType.SPECIALISATION_GAINED:
            activity = event.data.get("activity", "?")
            dashboard.add_event(f"Agent {event.agent_id} specialised in {activity}", "cyan")

        elif event.type == BusEventType.STRUCTURE_BUILT:
            stype = event.data.get("structure_type", "?")
            dashboard.add_event(f"Agent {event.agent_id} built {stype}", "dim")

        elif event.type == BusEventType.MESSAGE_SENT:
            if log_level == "DEBUG":
                sender = event.data.get("sender_id", "?")
                receiver = event.data.get("receiver_id", "?")
                dashboard.add_event(f"Agent {sender} → Agent {receiver}", "dim")

        elif event.type == BusEventType.AGENT_ARRIVED:
            aid = event.data.get("agent_id", "?")
            dashboard.add_event(f"New agent {aid} arrived", "cyan")

        elif event.type == BusEventType.ENVIRONMENTAL_SHIFT:
            severity = event.data.get("severity", "?")
            dashboard.add_event(f"Environmental shift ({severity})", "yellow bold")

    return handle
