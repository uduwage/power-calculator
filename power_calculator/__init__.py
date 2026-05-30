"""Stable public package exports for ``power_calculator``.

During Phase 0 refactoring, keep the top-level package surface aligned with the
existing binary-first API. Shared core modules remain internal until they are
intentionally promoted.
"""

from power_calculator.binary_power import (
    SampleSizeInput,
    SampleSizeResult,
    calculate_sample_size,
)
from power_calculator.duration import (
    DurationEstimate,
    GroupDurationEstimate,
    estimate_duration,
    estimate_duration_by_group,
    estimate_duration_equal_groups,
)

__all__ = [
    "SampleSizeInput",
    "SampleSizeResult",
    "calculate_sample_size",
    "DurationEstimate",
    "GroupDurationEstimate",
    "estimate_duration",
    "estimate_duration_equal_groups",
    "estimate_duration_by_group",
]
