"""Binary-metric A/B(/n) sample size calculations.

Notes:
    Uses `@dataclass` models as a clear data contract between the CLI layer
    and core calculation logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from power_calculator.core.allocation import (
    _parse_allocation as _parse_shared_allocation,
)
from power_calculator.core.binary import calculate_binary_sample_size_details
from power_calculator.core.models import (
    BinaryDesignInputs,
    DesignRequest,
    ExperimentDesignSettings,
)
from power_calculator.core.types import Alternative, Correction


@dataclass(frozen=True)
class SampleSizeInput:
    """Input configuration for binary sample-size calculations.

    Notes:
        - Groups all calculator inputs in one typed object.
        - `baseline_rate_pct` and `mde_pct` are percentage points.
        - `allocation` is `control:treatment`, for example `50:50` or `40:60`.
    """

    alternative: Alternative = "two-sided"
    confidence_level: float = 0.95
    power: float = 0.8
    groups: int = 2
    correction: Correction = "none"
    baseline_rate_pct: float = 10.0
    mde_pct: float = 2.0
    allocation: str = "50:50"


@dataclass(frozen=True)
class SampleSizeResult:
    """Output from the sample size calculation.

    Notes:
        Returns named fields (for example, `control_sample_size` and
        `overall_total`) instead of positional values.
    """

    alpha: float
    adjusted_alpha: float
    comparisons: int
    control_allocation: float
    treatment_allocation: float
    baseline_rate: float
    variant_rate: float
    mde: float
    control_sample_size: int
    treatment_sample_size: int
    per_comparison_total: int
    overall_total: int


def _parse_allocation(allocation: str, groups: int) -> list[float]:
    """Backward-compatible import location for allocation parsing."""
    return _parse_shared_allocation(allocation, groups)


def calculate_sample_size(config: SampleSizeInput) -> SampleSizeResult:
    """Calculate minimum sample size for binary A/B(/n) tests.

    Uses the normal approximation for difference in two proportions.
    For ``groups > 2`` this assumes one control group and ``groups - 1``
    treatment groups compared pairwise to control.

    Args:
        config: Sample-size configuration for binary A/B(/n) calculation.

    Returns:
        Sample-size result including per-group and overall totals.

    Raises:
        ValueError: If configuration values are outside valid ranges.

    References:
        - Casagrande, J. T., Pike, M. C., & Smith, P. G. (1978).
          https://doi.org/10.2307/2530613
        - Fleiss, J. L., Tytun, A., & Ury, H. K. (1980).
          https://doi.org/10.2307/2529990
    """
    request = DesignRequest(
        metric_family="binary",
        settings=ExperimentDesignSettings(
            alternative=config.alternative,
            confidence_level=config.confidence_level,
            power=config.power,
            groups=config.groups,
            correction=config.correction,
            allocation=config.allocation,
        ),
        inputs=BinaryDesignInputs(
            baseline_rate_pct=config.baseline_rate_pct,
            mde_pct=config.mde_pct,
        ),
    )
    details = calculate_binary_sample_size_details(request)

    return SampleSizeResult(
        alpha=details.alpha,
        adjusted_alpha=details.adjusted_alpha,
        comparisons=details.comparisons,
        control_allocation=details.control_allocation,
        treatment_allocation=details.treatment_allocation,
        baseline_rate=details.baseline_rate,
        variant_rate=details.variant_rate,
        mde=details.mde,
        control_sample_size=details.control_sample_size,
        treatment_sample_size=details.treatment_sample_size,
        per_comparison_total=details.per_comparison_total,
        overall_total=details.overall_total,
    )
