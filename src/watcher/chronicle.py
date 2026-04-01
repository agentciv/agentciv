"""Append-only JSONL storage + in-memory query for the Watcher chronicle.

Every observation the Watcher produces — tick reports, narratives,
milestones, and ethical flags — is recorded here for retrospective
analysis and display.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("agent_civilisation.watcher.chronicle")


class Chronicle:
    """Persistent append-only log of Watcher observations.

    Entries are stored as JSONL (one JSON object per line) and also
    kept in memory for fast queries during a running simulation.
    """

    def __init__(self, log_path: str) -> None:
        self._log_path = log_path
        self._entries: list[dict] = []

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record(self, entry_type: str, tick: int, data: dict) -> None:
        """Append an entry to the chronicle (file + in-memory).

        Args:
            entry_type: One of "tick_report", "narrative", "milestone",
                        "ethical_flag".
            tick: The simulation tick when this entry was produced.
            data: Arbitrary dict payload for the entry.
        """
        entry = {
            "type": entry_type,
            "tick": tick,
            "timestamp": time.time(),
            "data": data,
        }
        self._entries.append(entry)
        self._append_to_file(entry)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_reports(
        self,
        since_tick: int = 0,
        until_tick: Optional[int] = None,
        type_filter: Optional[str] = None,
    ) -> list[dict]:
        """Return entries matching the given filters."""
        results: list[dict] = []
        for e in self._entries:
            if e["tick"] < since_tick:
                continue
            if until_tick is not None and e["tick"] > until_tick:
                continue
            if type_filter is not None and e["type"] != type_filter:
                continue
            results.append(e)
        return results

    def get_milestones(self) -> list[dict]:
        """Return all milestone entries."""
        return [e for e in self._entries if e["type"] == "milestone"]

    def get_latest_narrative(self) -> Optional[dict]:
        """Return the most recent narrative entry, or None."""
        for e in reversed(self._entries):
            if e["type"] == "narrative":
                return e
        return None

    def get_ethical_flags(self) -> list[dict]:
        """Return all ethical flag entries."""
        return [e for e in self._entries if e["type"] == "ethical_flag"]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load existing JSONL file on startup (if it exists)."""
        if not os.path.exists(self._log_path):
            return
        try:
            with open(self._log_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        self._entries.append(entry)
                    except json.JSONDecodeError:
                        logger.warning("Skipping malformed JSONL line in chronicle")
            logger.info(
                "Chronicle loaded: %d entries from %s",
                len(self._entries),
                self._log_path,
            )
        except Exception:
            logger.exception("Failed to load chronicle from %s", self._log_path)

    def _append_to_file(self, entry: dict) -> None:
        """Append a single JSON line to the chronicle file."""
        try:
            os.makedirs(os.path.dirname(self._log_path), exist_ok=True)
            with open(self._log_path, "a") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception:
            logger.exception("Failed to write chronicle entry to %s", self._log_path)
