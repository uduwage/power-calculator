"""Shared data models for experiment design and evaluation workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from .types import Alternative, Correction, MetricFamily

DesignInputsType = TypeVar("DesignInputsType")


@dataclass(frozen=True)
class ExperimentDesignSettings:
    """Shared experiment settings reused across metric families."""

    alternative: Alternative = "two-sided"
    confidence_level: float = 0.95
    power: float = 0.8
    groups: int = 2
    correction: Correction = "none"
    allocation: str = "50:50"


@dataclass(frozen=True)
class BinaryDesignInputs:
    """Binary-specific inputs for experiment design calculations."""

    baseline_rate_pct: float = 10.0
    mde_pct: float = 2.0


@dataclass(frozen=True)
class DesignRequest(Generic[DesignInputsType]):
    """Shared request envelope for design calculations.

    Notes:
        Combines the metric family, shared experiment settings, and the
        family-specific design inputs required by a calculator implementation.
    """

    metric_family: MetricFamily
    settings: ExperimentDesignSettings
    inputs: DesignInputsType


@dataclass(frozen=True)
class DesignSampleSizeResult:
    """Shared sample-size result for design workflows.

    Notes:
        This model intentionally keeps only cross-family outputs. Metric-family
        implementations can layer richer compatibility results on top of it.
    """

    metric_family: MetricFamily
    group_sample_sizes: dict[str, int]
    overall_total: int
    per_comparison_total: int | None = None
    alpha: float | None = None
    adjusted_alpha: float | None = None
    comparisons: int = 1


__all__ = [
    "ExperimentDesignSettings",
    "BinaryDesignInputs",
    "DesignRequest",
    "DesignSampleSizeResult",
]
