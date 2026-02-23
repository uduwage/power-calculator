"""Helpers for estimating experiment duration."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isclose
from typing import Dict, Mapping


@dataclass(frozen=True)
class DurationEstimate:
    """Duration estimate for a total required sample size."""

    total_sample_size: int
    expected_daily_eligible_users: float
    days_required: int


@dataclass(frozen=True)
class GroupDurationEstimate:
    """Duration estimate when sample sizes and traffic splits are group-specific."""

    expected_daily_eligible_users: float
    days_per_group: Dict[str, int]
    days_required: int


def _validate_daily_inputs(daily_users: float, eligible_rate: float) -> float:
    if daily_users <= 0:
        raise ValueError("daily_users must be positive.")
    if not (0 < eligible_rate <= 1):
        raise ValueError("eligible_rate must be in (0, 1].")
    return daily_users * eligible_rate


def estimate_duration(
    total_sample_size: int, daily_users: float, eligible_rate: float = 1.0
) -> DurationEstimate:
    """Estimate calendar days needed to collect a total required sample size."""
    if total_sample_size <= 0:
        raise ValueError("total_sample_size must be positive.")

    daily_eligible = _validate_daily_inputs(daily_users, eligible_rate)
    days = ceil(total_sample_size / daily_eligible)
    return DurationEstimate(
        total_sample_size=total_sample_size,
        expected_daily_eligible_users=daily_eligible,
        days_required=days,
    )


def estimate_duration_equal_groups(
    per_group_sample_size: int,
    groups: int,
    daily_users: float,
    eligible_rate: float = 1.0,
) -> DurationEstimate:
    """Estimate duration when all groups have the same required sample size."""
    if per_group_sample_size <= 0:
        raise ValueError("per_group_sample_size must be positive.")
    if groups < 2:
        raise ValueError("groups must be at least 2.")
    return estimate_duration(
        total_sample_size=per_group_sample_size * groups,
        daily_users=daily_users,
        eligible_rate=eligible_rate,
    )


def estimate_duration_by_group(
    group_sample_sizes: Mapping[str, int],
    daily_users: float,
    traffic_shares: Mapping[str, float],
    eligible_rate: float = 1.0,
) -> GroupDurationEstimate:
    """Estimate duration for unequal sample-size and traffic-share allocations.

    ``group_sample_sizes`` and ``traffic_shares`` must have the same non-empty keys.
    Share values must be positive and sum to 1.
    """

    if not group_sample_sizes:
        raise ValueError("group_sample_sizes must not be empty.")
    if set(group_sample_sizes.keys()) != set(traffic_shares.keys()):
        raise ValueError("group_sample_sizes and traffic_shares keys must match.")

    total_share = 0.0
    for group, sample_size in group_sample_sizes.items():
        if sample_size <= 0:
            raise ValueError("All group sample sizes must be positive.")
        share = traffic_shares[group]
        if share <= 0:
            raise ValueError("All traffic shares must be positive.")
        total_share += share

    if not isclose(total_share, 1.0, rel_tol=1e-6, abs_tol=1e-9):
        raise ValueError("traffic_shares must sum to 1.")

    daily_eligible = _validate_daily_inputs(daily_users, eligible_rate)
    days_per_group: Dict[str, int] = {}
    for group, sample_size in group_sample_sizes.items():
        days_per_group[group] = ceil(sample_size / (daily_eligible * traffic_shares[group]))

    return GroupDurationEstimate(
        expected_daily_eligible_users=daily_eligible,
        days_per_group=days_per_group,
        days_required=max(days_per_group.values()),
    )


def estimate_duration_days_equal_groups(
    per_group_n: int,
    n_groups: int,
    daily_eligible_users: float,
    eligibility_fraction: float = 1.0,
) -> int:
    """Backward-compatible alias for the original advanced helper."""
    return estimate_duration_equal_groups(
        per_group_sample_size=per_group_n,
        groups=n_groups,
        daily_users=daily_eligible_users,
        eligible_rate=eligibility_fraction,
    ).days_required


def estimate_duration_days_custom_split(
    group_ns: Mapping[str, int],
    daily_eligible_users: float,
    traffic_shares: Mapping[str, float],
    eligibility_fraction: float = 1.0,
) -> Dict[str, object]:
    """Backward-compatible alias for the original custom-split helper."""
    result = estimate_duration_by_group(
        group_sample_sizes=group_ns,
        daily_users=daily_eligible_users,
        traffic_shares=traffic_shares,
        eligible_rate=eligibility_fraction,
    )
    return {"days_per_group": result.days_per_group, "max_days": result.days_required}
