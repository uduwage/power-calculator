import pytest

from power_calculator.binary_power import SampleSizeInput, calculate_sample_size

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

def test_calculate_sample_size_groups_gt_2_with_40_60_current_behavior() -> None:
    result = calculate_sample_size(
        SampleSizeInput(
            alternative="two-sided",
            confidence_level=0.95,
            power=0.80,
            groups=4,
            correction="none",
            baseline_rate_pct=10.0,
            mde_pct=2.0,
            allocation="40:60",            
        )
    )

    assert result.comparisons == 3
    assert result.control_allocation == pytest.approx(0.4)
    assert result.treatment_allocation == pytest.approx(0.6)
    assert result.control_sample_size == 3186
    assert result.treatment_sample_size == 4779
    assert result.per_comparison_total == 7965
    assert result.overall_total == 17523

def test_calculate_sample_size_rejects_three_part_allocation_today() -> None:
    with pytest.raises(
        ValueError,
        match=r"Allocation must be in 'control:treatment' format \(e\.g\. 50:50\)\.",
    ):
        calculate_sample_size(
            SampleSizeInput(
                groups=2,
                baseline_rate_pct=10.0,
                mde_pct=2.0,
                allocation="33:33:34",
            )
        )