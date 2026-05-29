import pytest

from power_calculator.core.base import MetricFamilyDesignCalculator
from power_calculator.core.binary import (
    BinaryDesignCalculator,
    calculate_binary_sample_size_details,
)
from power_calculator.core.models import (
    BinaryDesignInputs,
    DesignRequest,
    ExperimentDesignSettings,
)


def test_calculate_binary_sample_size_details_matches_current_ab_behavior() -> None:
    request = DesignRequest(
        metric_family="binary",
        settings=ExperimentDesignSettings(
            alternative="two-sided",
            confidence_level=0.95,
            power=0.80,
            groups=2,
            correction="none",
            allocation="50:50",
        ),
        inputs=BinaryDesignInputs(
            baseline_rate_pct=10.0,
            mde_pct=2.0,
        ),
    )

    result = calculate_binary_sample_size_details(request)

    assert result.comparisons == 1
    assert result.control_allocation == pytest.approx(0.5)
    assert result.treatment_allocation == pytest.approx(0.5)
    assert result.control_sample_size == 3841
    assert result.treatment_sample_size == 3841
    assert result.per_comparison_total == 7682
    assert result.overall_total == 7682


def test_binary_design_calculator_returns_shared_result_for_multivariant() -> None:
    calculator = BinaryDesignCalculator()
    request = DesignRequest(
        metric_family="binary",
        settings=ExperimentDesignSettings(
            alternative="two-sided",
            confidence_level=0.95,
            power=0.80,
            groups=4,
            correction="none",
            allocation="40:60:60:60",
        ),
        inputs=BinaryDesignInputs(
            baseline_rate_pct=10.0,
            mde_pct=2.0,
        ),
    )

    assert isinstance(calculator, MetricFamilyDesignCalculator)
    result = calculator.calculate_sample_size(request)

    assert result.metric_family == "binary"
    assert result.comparisons == 3
    assert result.group_sample_sizes == {
        "control": 3186,
        "treatment_1": 4779,
        "treatment_2": 4779,
        "treatment_3": 4779,
    }
    assert result.per_comparison_total == 7965
    assert result.overall_total == 17523


def test_calculate_binary_sample_size_details_rejects_wrong_metric_family() -> None:
    request = DesignRequest(
        metric_family="continuous_mean",
        settings=ExperimentDesignSettings(),
        inputs=BinaryDesignInputs(),
    )

    with pytest.raises(
        ValueError,
        match=r"Binary design requests must use metric_family='binary'\.",
    ):
        calculate_binary_sample_size_details(request)
