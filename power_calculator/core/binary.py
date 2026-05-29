"""Binary metric-family implementation within the shared core architecture."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, sqrt

from .allocation import _parse_allocation
from .base import MetricFamilyDesignCalculator
from .models import BinaryDesignInputs, DesignRequest, DesignSampleSizeResult
from .stats import _adjusted_alpha, _critical_z, _normal_ppf


@dataclass(frozen=True)
class BinaryDesignSampleSizeDetails:
    """Binary-specific sample-size details used by compatibility layers."""

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


def _validate_binary_design_request(
    request: DesignRequest[BinaryDesignInputs],
) -> None:
    """Validate shared and binary-specific inputs for binary design."""
    settings = request.settings
    inputs = request.inputs

    if request.metric_family != "binary":
        raise ValueError("Binary design requests must use metric_family='binary'.")
    if not (0 < settings.confidence_level < 1):
        raise ValueError("confidence_level must be between 0 and 1.")
    if not (0 < settings.power < 1):
        raise ValueError("power must be between 0 and 1.")
    if settings.groups < 2:
        raise ValueError("groups must be at least 2.")
    if not (0 < inputs.baseline_rate_pct < 100):
        raise ValueError("baseline_rate_pct must be between 0 and 100.")
    if not (0 < inputs.mde_pct < 100):
        raise ValueError("mde_pct must be between 0 and 100.")


def _build_shared_sample_size_result(
    details: BinaryDesignSampleSizeDetails,
) -> DesignSampleSizeResult:
    """Convert binary-specific sample-size details into the shared result model."""
    group_sample_sizes = {"control": details.control_sample_size}
    for treatment_index in range(1, details.comparisons + 1):
        group_sample_sizes[f"treatment_{treatment_index}"] = (
            details.treatment_sample_size
        )

    return DesignSampleSizeResult(
        metric_family="binary",
        group_sample_sizes=group_sample_sizes,
        overall_total=details.overall_total,
        per_comparison_total=details.per_comparison_total,
        alpha=details.alpha,
        adjusted_alpha=details.adjusted_alpha,
        comparisons=details.comparisons,
    )


def calculate_binary_sample_size_details(
    request: DesignRequest[BinaryDesignInputs],
) -> BinaryDesignSampleSizeDetails:
    """Calculate binary sample size while preserving binary-specific details.

    Uses the normal approximation for difference in two proportions.
    For ``groups > 2`` this assumes one control group and ``groups - 1``
    treatment groups compared pairwise to control.

    Args:
        request: Shared design request for binary sample-size calculation.

    Returns:
        Binary-specific sample-size details used by compatibility layers.

    Raises:
        ValueError: If request values are outside valid ranges.

    References:
        - Casagrande, J. T., Pike, M. C., & Smith, P. G. (1978).
          https://doi.org/10.2307/2530613
        - Fleiss, J. L., Tytun, A., & Ury, H. K. (1980).
          https://doi.org/10.2307/2529990
    """
    _validate_binary_design_request(request)
    settings = request.settings
    inputs = request.inputs

    allocation_shares = _parse_allocation(settings.allocation, settings.groups)
    control_share = allocation_shares[0]
    treatment_shares = allocation_shares[1:]

    first_treatment_share = treatment_shares[0]
    if any(share != first_treatment_share for share in treatment_shares[1:]):
        raise ValueError("Non-uniform treatment allocations are not supported yet.")

    pair_total = control_share + treatment_shares[0]
    control_allocation = control_share / pair_total
    treatment_allocation = treatment_shares[0] / pair_total
    treatment_to_control_ratio = treatment_allocation / control_allocation

    baseline_rate = inputs.baseline_rate_pct / 100.0
    minimum_detectable_effect = inputs.mde_pct / 100.0
    variant_rate = baseline_rate + minimum_detectable_effect
    if not (0 < variant_rate < 1):
        raise ValueError(
            "baseline_rate_pct + mde_pct must stay below 100%. "
            "Use an MDE that keeps the treatment rate in (0, 100)."
        )

    alpha = 1 - settings.confidence_level
    adjusted_alpha, comparisons = _adjusted_alpha(
        alpha, settings.groups, settings.correction
    )
    if not (0 < adjusted_alpha < 1):
        raise ValueError("Adjusted alpha is invalid. Check groups/correction values.")

    z_alpha = _critical_z(adjusted_alpha, settings.alternative)
    z_beta = _normal_ppf(settings.power)

    pooled_rate = (baseline_rate + variant_rate) / 2
    null_term = z_alpha * sqrt(
        (1 + treatment_to_control_ratio) * pooled_rate * (1 - pooled_rate)
    )
    alternative_term = z_beta * sqrt(
        treatment_to_control_ratio * baseline_rate * (1 - baseline_rate)
        + variant_rate * (1 - variant_rate)
    )

    control_sample_size = ceil(
        ((null_term + alternative_term) ** 2)
        / (treatment_to_control_ratio * (minimum_detectable_effect**2))
    )
    treatment_sample_size = ceil(control_sample_size * treatment_to_control_ratio)
    per_comparison_total = control_sample_size + treatment_sample_size
    overall_total = control_sample_size + (settings.groups - 1) * treatment_sample_size

    return BinaryDesignSampleSizeDetails(
        alpha=alpha,
        adjusted_alpha=adjusted_alpha,
        comparisons=comparisons,
        control_allocation=control_allocation,
        treatment_allocation=treatment_allocation,
        baseline_rate=baseline_rate,
        variant_rate=variant_rate,
        mde=minimum_detectable_effect,
        control_sample_size=control_sample_size,
        treatment_sample_size=treatment_sample_size,
        per_comparison_total=per_comparison_total,
        overall_total=overall_total,
    )


class BinaryDesignCalculator(MetricFamilyDesignCalculator[BinaryDesignInputs]):
    """Binary implementation of the shared design calculator contract."""

    def calculate_sample_size(
        self,
        request: DesignRequest[BinaryDesignInputs],
    ) -> DesignSampleSizeResult:
        """Calculate sample size for a binary metric-family design request."""
        return _build_shared_sample_size_result(
            calculate_binary_sample_size_details(request)
        )


__all__ = [
    "BinaryDesignCalculator",
    "BinaryDesignSampleSizeDetails",
    "calculate_binary_sample_size_details",
]
