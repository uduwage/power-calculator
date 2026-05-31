"""Shared statistical utilities for power and sample size calculations."""

from __future__ import annotations

from math import log, sqrt

from .types import Alternative, Correction


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
    TODO: It looks like SciPy supports this approximation calculation.
    Once the refactoring is done look into this.
    Also, Once SciPy is added as a dependency in the future, consider delegating
    to its normal inverse CDF implementation (such as
    `scipy.stats.norm.ppf`) instead of maintaining this approximation.

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


__all__ = [
    "_adjusted_alpha",
    "_critical_z",
    "_normal_ppf",
]
