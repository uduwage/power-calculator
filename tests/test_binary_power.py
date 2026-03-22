import pytest

from power_calculator.binary_power import (
    SampleSizeInput,
    _parse_allocation,
    calculate_sample_size,
)

def test_calculate_sample_size_ab_50_50_current_behavior() -> None:
    result = calculate_sample_size(
        SampleSizeInput(
            alternative="two-sided",
            confidence_level=0.95,
            power=0.80,
            groups=2,
            correction="none",
            baseline_rate_pct=10.0,
            mde_pct=2.0,
            allocation="50:50",
        )
    )

    assert result.comparisons == 1
    assert result.control_allocation == pytest.approx(0.5)
    assert result.treatment_allocation == pytest.approx(0.5)
    assert result.control_sample_size == 3841
    assert result.treatment_sample_size == 3841
    assert result.per_comparison_total == 7682
    assert result.overall_total == 7682

def test_calculate_sample_size_groups_gt_2_with_explicit_allocation() -> None:
    result = calculate_sample_size(
        SampleSizeInput(
            alternative="two-sided",
            confidence_level=0.95,
            power=0.80,
            groups=4,
            correction="none",
            baseline_rate_pct=10.0,
            mde_pct=2.0,
            allocation="40:60:60:60",
        )
    )

    assert result.comparisons == 3
    assert result.control_allocation == pytest.approx(0.4)
    assert result.treatment_allocation == pytest.approx(0.6)
    assert result.control_sample_size == 3186
    assert result.treatment_sample_size == 4779
    assert result.per_comparison_total == 7965
    assert result.overall_total == 17523


def test_calculate_sample_size_rejects_non_uniform_treatment_allocations() -> None:
    with pytest.raises(
        ValueError,
        match=r"Non-uniform treatment allocations are not supported yet\.",
    ):
        calculate_sample_size(
            SampleSizeInput(
                groups=3,
                baseline_rate_pct=10.0,
                mde_pct=2.0,
                allocation="34:40:26",
            )
        )


def test_calculate_sample_size_rejects_two_part_allocation_for_groups_gt_2() -> None:
    with pytest.raises(
        ValueError,
        match=r"Allocation has 2 values but groups=4\.",
    ):
        calculate_sample_size(
            SampleSizeInput(
                groups=4,
                baseline_rate_pct=10.0,
                mde_pct=2.0,
                allocation="40:60",
            )
        )


def test_calculate_sample_size_rejects_three_part_allocation_today() -> None:
    with pytest.raises(
        ValueError,
        match=r"For 2 groups, provide exactly two values like 'control:treatment'",
    ):
        calculate_sample_size(
            SampleSizeInput(
                groups=2,
                baseline_rate_pct=10.0,
                mde_pct=2.0,
                allocation="33:33:34",
            )
        )

def test_parse_allocation_explicit_multivariant() -> None:
    shares = _parse_allocation("33:33:34", groups=3)
    assert len(shares) == 3
    assert sum(shares) == pytest.approx(1.0)
    assert shares[0] == pytest.approx(0.33, rel=1e-3)
    assert shares[1] == pytest.approx(0.33, rel=1e-3)
    assert shares[2] == pytest.approx(0.34, rel=1e-3)


def test_parse_allocation_two_part_for_two_groups() -> None:
    shares = _parse_allocation("40:60", groups=2)
    assert len(shares) == 2
    assert sum(shares) == pytest.approx(1.0)
    assert shares[0] == pytest.approx(0.4)
    assert shares[1] == pytest.approx(0.6)


def test_parse_allocation_rejects_two_part_for_groups_gt_2() -> None:
    with pytest.raises(
        ValueError,
        match=r"For groups > 2, provide exactly one value per group",
    ):
        _parse_allocation("40:60", groups=4)
