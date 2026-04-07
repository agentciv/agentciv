"""Structured emergence metrics for Agent Civilisation.

Extracts quantifiable metrics from a completed simulation run,
enabling automated comparison across different configurations.
"""

from .emergence import EmergenceScore, compute_emergence
from .run_record import SimulationRunRecord

__all__ = ["EmergenceScore", "compute_emergence", "SimulationRunRecord"]
