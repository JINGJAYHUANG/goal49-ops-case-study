"""Synthetic reference implementation for the Goal49 operations case study."""

from .engine import (
    Decision,
    HealthResult,
    IntegrityError,
    ProviderBatch,
    Snapshot,
    build_snapshot,
    finalize,
    health_check,
    verify_snapshot,
)

__all__ = [
    "Decision",
    "HealthResult",
    "IntegrityError",
    "ProviderBatch",
    "Snapshot",
    "build_snapshot",
    "finalize",
    "health_check",
    "verify_snapshot",
]

__version__ = "0.1.0"
