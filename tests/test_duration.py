import pytest

from power_calculator.duration import (
    estimate_duration,
    estimate_duration_by_group,
    estimate_duration_days_custom_split,
    estimate_duration_days_equal_groups,
    estimate_duration_equal_groups,
)


def test_estimate_duration_success_rounds_up() -> None:
    result = estimate_duration(
        total_sample_size=1000, daily_users=333, eligible_rate=0.5
    )
    assert result.total_sample_size == 1000
    assert result.expected_daily_eligible_users == pytest.approx(166.5)
    assert result.days_required == 7


def test_estimate_duration_rejects_invalid_total_sample_size() -> None:
    with pytest.raises(ValueError, match="total_sample_size must be positive"):
        estimate_duration(total_sample_size=0, daily_users=1000, eligible_rate=1.0)


@pytest.mark.parametrize("daily_users", [0, -10])
def test_estimate_duration_rejects_invalid_daily_users(daily_users: float) -> None:
    with pytest.raises(ValueError, match="daily_users must be positive"):
        estimate_duration(
            total_sample_size=100, daily_users=daily_users, eligible_rate=1.0
        )


@pytest.mark.parametrize("eligible_rate", [0, -0.1, 1.1])
def test_estimate_duration_rejects_invalid_eligible_rate(eligible_rate: float) -> None:
    with pytest.raises(ValueError, match="eligible_rate must be in"):
        estimate_duration(
            total_sample_size=100, daily_users=1000, eligible_rate=eligible_rate
        )


def test_estimate_duration_equal_groups_success() -> None:
    result = estimate_duration_equal_groups(
        per_group_sample_size=500, groups=3, daily_users=1000, eligible_rate=0.5
    )
    assert result.total_sample_size == 1500
    assert result.days_required == 3


def test_estimate_duration_equal_groups_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="per_group_sample_size must be positive"):
        estimate_duration_equal_groups(0, 2, 1000, 1.0)
    with pytest.raises(ValueError, match="groups must be at least 2"):
        estimate_duration_equal_groups(100, 1, 1000, 1.0)


def test_estimate_duration_by_group_success() -> None:
    result = estimate_duration_by_group(
        group_sample_sizes={"control": 1000, "treatment_1": 1200},
        daily_users=1000,
        traffic_shares={"control": 0.4, "treatment_1": 0.6},
        eligible_rate=0.5,
    )
    assert result.expected_daily_eligible_users == pytest.approx(500.0)
    assert result.days_per_group == {"control": 5, "treatment_1": 4}
    assert result.days_required == 5


def test_estimate_duration_by_group_rejects_empty_sample_sizes() -> None:
    with pytest.raises(ValueError, match="group_sample_sizes must not be empty"):
        estimate_duration_by_group({}, 1000, {}, 1.0)


def test_estimate_duration_by_group_rejects_mismatched_keys() -> None:
    with pytest.raises(ValueError, match="keys must match"):
        estimate_duration_by_group(
            {"control": 1000, "treatment_1": 1200},
            1000,
            {"control": 0.5, "treatment_2": 0.5},
            1.0,
        )


def test_estimate_duration_by_group_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="sample sizes must be positive"):
        estimate_duration_by_group(
            {"control": 0, "treatment_1": 1000},
            1000,
            {"control": 0.5, "treatment_1": 0.5},
            1.0,
        )
    with pytest.raises(ValueError, match="traffic shares must be positive"):
        estimate_duration_by_group(
            {"control": 1000, "treatment_1": 1000},
            1000,
            {"control": 0.0, "treatment_1": 1.0},
            1.0,
        )
    with pytest.raises(ValueError, match="traffic_shares must sum to 1"):
        estimate_duration_by_group(
            {"control": 1000, "treatment_1": 1000},
            1000,
            {"control": 0.3, "treatment_1": 0.3},
            1.0,
        )


def test_backward_compatible_wrappers() -> None:
    days = estimate_duration_days_equal_groups(
        per_group_n=500,
        n_groups=3,
        daily_eligible_users=1000,
        eligibility_fraction=0.5,
    )
    assert days == 3

    custom = estimate_duration_days_custom_split(
        group_ns={"control": 1000, "treatment_1": 1200},
        daily_eligible_users=1000,
        traffic_shares={"control": 0.4, "treatment_1": 0.6},
        eligibility_fraction=0.5,
    )
    assert custom["days_per_group"] == {"control": 5, "treatment_1": 4}
    assert custom["max_days"] == 5
