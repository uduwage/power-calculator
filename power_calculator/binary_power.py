"""Binary-metric A/B(/n) sample size calculations.

Notes:
    Uses `@dataclass` models as a clear data contract between the CLI layer
    and core calculation logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, sqrt

from power_calculator.core.stats import _adjusted_alpha, _critical_z, _normal_ppf
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
    """Parse allocation into normalized per-group shares.

    Supported input forms:
    - groups=2: `control:treatment` (e.g. `50:50`)
    - groups>2: explicit `control:t1:t2:...` with exactly `groups` values
      (e.g. `50:25:25` for 3 groups).

    Args:
        allocation: Allocation text separated by `:`.
        groups: Total number of experiment groups, including control.

    Returns:
        Normalized per-group shares as `[control, treatment_1, ...]`.

    Raises:
        ValueError: If parsing fails, count does not match allowed formats,
            or any value is non-positive.
    """
    try:
        weights = [float(part.strip()) for part in allocation.split(":")]
    except (AttributeError, ValueError) as exc:
        raise ValueError(
            "Allocation must be in 'control:treatment' or "
            "'control:t1:t2:...' format (i.e. 50:50 or 33:33:34)."
        ) from exc

    if len(weights) < 2:
        raise ValueError("Allocation must include at least control and one treatment.")
    if any(weight <= 0 for weight in weights):
        raise ValueError("Allocation values must all be positive.")

    if len(weights) == 2 and groups == 2 or len(weights) == groups:
        expanded = weights
    else:
        if groups == 2:
            guidance = (
                "For 2 groups, provide exactly two values like "
                "'control:treatment' (e.g. 50:50)."
            )
        else:
            guidance = (
                "For groups > 2, provide exactly one value per group "
                "(e.g. 50:25:25)."
            )
        raise ValueError(
            f"Allocation has {len(weights)} values but groups={groups}. " + guidance
        )
    total = sum(expanded)
    return [weight / total for weight in expanded]
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
    if not (0 < config.confidence_level < 1):
        raise ValueError("confidence_level must be between 0 and 1.")
    if not (0 < config.power < 1):
        raise ValueError("power must be between 0 and 1.")
    if config.groups < 2:
        raise ValueError("groups must be at least 2.")
    if not (0 < config.baseline_rate_pct < 100):
        raise ValueError("baseline_rate_pct must be between 0 and 100.")
    if not (0 < config.mde_pct < 100):
        raise ValueError("mde_pct must be between 0 and 100.")

    allocation_shares = _parse_allocation(config.allocation, config.groups)
    control_share = allocation_shares[0]
    treatment_shares = allocation_shares[1:]

    first_treatment_share = treatment_shares[0]
    if any(share != first_treatment_share for share in treatment_shares[1:]):
        raise ValueError("Non-uniform treatment allocations are not supported yet.")

    pair_total = control_share + treatment_shares[0]
    control_alloc = control_share / pair_total
    treatment_alloc = treatment_shares[0] / pair_total
    ratio = treatment_alloc / control_alloc

    baseline = config.baseline_rate_pct / 100.0
    mde = config.mde_pct / 100.0
    variant = baseline + mde
    if not (0 < variant < 1):
        raise ValueError(
            "baseline_rate_pct + mde_pct must stay below 100%. "
            "Use an MDE that keeps the treatment rate in (0, 100)."
        )

    alpha = 1 - config.confidence_level
    adjusted_alpha, comparisons = _adjusted_alpha(
        alpha, config.groups, config.correction
    )
    if not (0 < adjusted_alpha < 1):
        raise ValueError("Adjusted alpha is invalid. Check groups/correction values.")

    z_alpha = _critical_z(adjusted_alpha, config.alternative)
    z_beta = _normal_ppf(config.power)

    pooled = (baseline + variant) / 2
    null_term = z_alpha * sqrt((1 + ratio) * pooled * (1 - pooled))
    alt_term = z_beta * sqrt(
        ratio * baseline * (1 - baseline) + variant * (1 - variant)
    )

    n_control = ceil(((null_term + alt_term) ** 2) / (ratio * (mde**2)))
    n_treatment = ceil(n_control * ratio)
    per_comparison_total = n_control + n_treatment
    overall_total = n_control + (config.groups - 1) * n_treatment

    return SampleSizeResult(
        alpha=alpha,
        adjusted_alpha=adjusted_alpha,
        comparisons=comparisons,
        control_allocation=control_alloc,
        treatment_allocation=treatment_alloc,
        baseline_rate=baseline,
        variant_rate=variant,
        mde=mde,
        control_sample_size=n_control,
        treatment_sample_size=n_treatment,
        per_comparison_total=per_comparison_total,
        overall_total=overall_total,
    )
