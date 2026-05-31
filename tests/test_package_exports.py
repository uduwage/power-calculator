import power_calculator
from power_calculator import (
    DurationEstimate,
    GroupDurationEstimate,
    SampleSizeInput,
    SampleSizeResult,
    calculate_sample_size,
    estimate_duration,
    estimate_duration_by_group,
    estimate_duration_equal_groups,
)


def test_top_level_package_exports_stable_binary_and_duration_api() -> None:
    assert SampleSizeInput is power_calculator.SampleSizeInput
    assert SampleSizeResult is power_calculator.SampleSizeResult
    assert calculate_sample_size is power_calculator.calculate_sample_size
    assert DurationEstimate is power_calculator.DurationEstimate
    assert GroupDurationEstimate is power_calculator.GroupDurationEstimate
    assert estimate_duration is power_calculator.estimate_duration
    assert (
        estimate_duration_equal_groups
        is power_calculator.estimate_duration_equal_groups
    )
    assert estimate_duration_by_group is power_calculator.estimate_duration_by_group


def test_top_level_package_does_not_export_shared_core_symbols_yet() -> None:
    assert "DesignRequest" not in power_calculator.__all__
    assert "DesignSampleSizeResult" not in power_calculator.__all__
    assert "MetricFamilyDesignCalculator" not in power_calculator.__all__
    assert not hasattr(power_calculator, "DesignRequest")
    assert not hasattr(power_calculator, "DesignSampleSizeResult")
    assert not hasattr(power_calculator, "MetricFamilyDesignCalculator")
