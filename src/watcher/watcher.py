"""Watcher orchestrator — ties together tick reports, narratives, milestones, and the chronicle.

Called once per tick from the TickEngine. Generates observations, detects
milestones, writes periodic narratives, and records everything in the
chronicle for retrospective analysis.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.config import SimulationConfig
from src.types import (
    BusEvent,
    BusEventType,
    EventBus,
    WorldState,
)
from src.watcher.chronicle import Chronicle
from src.watcher.chronicler import Chronicler
from src.watcher.milestone import MilestoneDetector
from src.watcher.narrative_report import generate_narrative
from src.watcher.tick_report import generate_tick_report

logger = logging.getLogger("agent_civilisation.watcher")

# How many tick reports to keep in the sliding window for narrative context
_REPORT_WINDOW = 100


class Watcher:
    """Orchestrates all Watcher subsystems.

    Usage::

        watcher = Watcher(config, event_bus, chronicle, llm_client)
        # In the tick loop, after all agent/world updates:
        await watcher.observe_tick(world_state, tick)
    """

    def __init__(
        self,
        config: SimulationConfig,
        event_bus: EventBus,
        chronicle: Chronicle,
        llm_client,
    ) -> None:
        self.config = config
        self.event_bus = event_bus
        self.chronicle = chronicle
        self.llm_client = llm_client
        self.milestone_detector = MilestoneDetector()
        self.chronicler = Chronicler(config, llm_client)
        self.recent_reports: list[dict] = []
        self._last_milestones: list[dict] = []  # From most recent tick

    async def observe_tick(self, world_state: WorldState, tick: int) -> None:
        """Run all Watcher observations for the given tick.

        Called once at the end of each tick, after all agent actions and
        world updates but before TICK_END is emitted.

        Steps:
          1. Generate tick report (pure data aggregation)
          2. Record tick report in chronicle + emit bus event
          3. Check milestones (heuristic + optional LLM commentary)
          4. Generate narrative if interval reached (LLM call)
        """
        # 1. Generate tick report
        report = generate_tick_report(world_state, self.event_bus, tick, self.config)

        # 2. Store in sliding window + chronicle
        self.recent_reports.append(report)
        if len(self.recent_reports) > _REPORT_WINDOW:
            self.recent_reports = self.recent_reports[-_REPORT_WINDOW:]

        self.chronicle.record("tick_report", tick, report)

        await self.event_bus.emit(BusEvent(
            type=BusEventType.WATCHER_TICK_REPORT,
            tick=tick,
            data=report,
        ))

        # 3. Check milestones
        self._last_milestones = []
        if self.config.enable_milestone_reports:
            try:
                milestones = await self.milestone_detector.check_milestones(
                    world_state, self.event_bus, tick, self.config, self.llm_client,
                )
                self._last_milestones = milestones
                for m in milestones:
                    # Ethical flags get a different entry type
                    if m.get("name") in ("Persistent Degradation", "Social Exclusion"):
                        self.chronicle.record("ethical_flag", tick, m)
                    else:
                        self.chronicle.record("milestone", tick, m)
                    await self.event_bus.emit(BusEvent(
                        type=BusEventType.WATCHER_MILESTONE,
                        tick=tick,
                        data=m,
                    ))
            except Exception:
                logger.exception("Milestone check failed at tick %d", tick)

        # 3b. Chronicler — live commentary (Attenborough mode)
        try:
            commentary = await self.chronicler.observe(
                world_state, report, self._last_milestones, tick
            )
            if commentary:
                self.chronicle.record("chronicler", tick, {"text": commentary})
                await self.event_bus.emit(BusEvent(
                    type=BusEventType.WATCHER_NARRATIVE,
                    tick=tick,
                    data={"text": commentary, "source": "chronicler"},
                ))
        except Exception:
            logger.exception("Chronicler failed at tick %d", tick)

        # 4. Narrative (every N ticks, after tick 0)
        interval = self.config.narrative_report_interval
        if interval > 0 and tick > 0 and tick % interval == 0:
            try:
                # Feed the last interval's worth of reports (or whatever we have)
                window = self.recent_reports[-interval:]
                narrative = await generate_narrative(
                    window, world_state, self.config, self.llm_client,
                )
                self.chronicle.record("narrative", tick, {"text": narrative})
                await self.event_bus.emit(BusEvent(
                    type=BusEventType.WATCHER_NARRATIVE,
                    tick=tick,
                    data={"text": narrative},
                ))
            except Exception:
                logger.exception("Narrative generation failed at tick %d", tick)
