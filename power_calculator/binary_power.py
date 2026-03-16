"""Binary-metric A/B(/n) sample size calculations.

Notes:
    Uses `@dataclass` models as a clear data contract between the CLI layer
    and core calculation logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log
from math import ceil, sqrt

Alternative = str
Correction = str


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
    """Parse allocation into normalized control and treatment shares.

    Supporting imput forms:
    - legacy: control:treatment (i.e: 40:60), expanded across groups-1 treatments.
    - explicit: control:t1:t2:... (must provide exactly `groups` values).

    Args:
        allocation (str): Allocation text in `control:treatment` format.
        groups (int): number of experimental groups including control.

    Returns:
        list of normalized treatment shares with length `groups - 1`

    Raises:
        ValueError: If format is invalid or values are non-positive.
    """
    try:
        weights = [float(part.strip()) for part in allocation.split(":")]
    except (AttributeError, ValueError) as exc:
        raise ValueError(
            "Allocation must be in 'control:treatment' or "
            "'control:t1:t2:...' format (i.e: 50:50 or 33:33:34)."
        ) from exc

    if len(weights) < 2:
        raise ValueError("Allocation must include at least control and on treatment.")
    if any(weight <= 0 for weight in weights):
        raise ValueError("Allocation values must all be positive")

    if len(weights) == 2:
        expanded = [weights[0]] + [weights[1]] * (groups - 1)
    elif len(weights) == groups:
        expanded = weights
    else:
        raise ValueError(
            f"Allocation has {len(weights)} values but groups={groups}."
            "use 2 values (control:treatment) or exactly one value per group."
        )
    total = sum(expanded)
    return [weight / total for weight in expanded]


def _adjusted_alpha(
    alpha: float, groups: int, correction: Correction
) -> tuple[float, int]:
    """Apply multiple-testing correction to alpha.

    Args:
        alpha: Raw type I error rate.
        groups: Total number of groups in the experiment.
        correction: Correction method (`none`, `bonferroni`, `sidak`).

    Returns:
        Tuple of `(adjusted_alpha, comparisons)` where comparisons is `groups - 1`.

    Raises:
        ValueError: If correction method is unsupported.

    References:
        - Sidak, Z. (1967). Rectangular confidence regions for the means of
          multivariate normal distributions.
          https://doi.org/10.1080/01621459.1967.10482935
        - Dunn, O. J. (1961). Multiple comparisons among means.
          https://doi.org/10.2307/2282330
    """
    comparisons = max(groups - 1, 1)
    if correction == "none" or comparisons == 1:
        return alpha, comparisons
    if correction == "bonferroni":
        return alpha / comparisons, comparisons
    if correction == "sidak":
        return 1 - (1 - alpha) ** (1 / comparisons), comparisons
    raise ValueError(f"Unsupported correction: {correction}")


def _critical_z(alpha: float, alternative: Alternative) -> float:
    """Return critical z-value for the configured alternative hypothesis.

    Args:
        alpha: Type I error rate after correction.
        alternative: `one-sided` or `two-sided`.

    Returns:
        Critical z-value.

    Raises:
        ValueError: If alternative is unsupported.
    """
    if alternative == "two-sided":
        return _normal_ppf(1 - alpha / 2)
    if alternative == "one-sided":
        return _normal_ppf(1 - alpha)
    raise ValueError(f"Unsupported alternative: {alternative}")


def _normal_ppf(probability: float) -> float:
    """Inverse CDF for standard normal distribution.

    Rational approximation from Peter John Acklam's algorithm.
    TODO: Research on how to use scikit-learn (distribution setup)

    Args:
        probability: Probability in the open interval `(0, 1)`.

    Returns:
        Standard normal quantile `z` such that `P(Z <= z) = probability`.

    Raises:
        ValueError: If probability is outside `(0, 1)`.

    References:
        - Acklam, P. J. (2000). Inverse normal CDF approximation note.
          http://web.archive.org/web/20151030215612/http://home.online.no/~pjacklam/notes/invnorm/
    """

    if not (0 < probability < 1):
        raise ValueError("probability must be in (0, 1).")

    # Coefficients in rational approximations.
    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    )

    lower_region = 0.02425
    upper_region = 1 - lower_region

    if probability < lower_region:
        q = sqrt(-2 * log(probability))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )

    if probability > upper_region:
        q = sqrt(-2 * log(1 - probability))
        return -(
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
        )

    q = probability - 0.5
    r = q * q
    return (
        (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
    ) / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


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

    if len({round(share, 12) for share in treatment_shares}) != 1:
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
