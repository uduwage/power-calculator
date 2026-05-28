from power_calculator.core.models import (
    BinaryDesignInputs,
    DesignRequest,
    DesignSampleSizeResult,
    ExperimentDesignSettings,
)


def test_design_request_separates_shared_settings_from_binary_inputs() -> None:
    settings = ExperimentDesignSettings(
        alternative="one-sided",
        confidence_level=0.90,
        power=0.85,
        groups=3,
        correction="sidak",
        allocation="40:30:30",
    )
    inputs = BinaryDesignInputs(baseline_rate_pct=12.0, mde_pct=1.5)

    request = DesignRequest(
        metric_family="binary",
        settings=settings,
        inputs=inputs,
    )

    assert request.metric_family == "binary"
    assert request.settings.groups == 3
    assert request.settings.allocation == "40:30:30"
    assert request.inputs.baseline_rate_pct == 12.0
    assert request.inputs.mde_pct == 1.5


def test_design_sample_size_result_captures_shared_outputs() -> None:
    result = DesignSampleSizeResult(
        metric_family="binary",
        group_sample_sizes={
            "control": 3186,
            "treatment_1": 4779,
            "treatment_2": 4779,
            "treatment_3": 4779,
        },
        overall_total=17523,
        per_comparison_total=7965,
        alpha=0.05,
        adjusted_alpha=0.05,
        comparisons=3,
    )

    assert result.group_sample_sizes["control"] == 3186
    assert sum(result.group_sample_sizes.values()) == result.overall_total
    assert result.per_comparison_total == 7965
    assert result.comparisons == 3


def test_design_sample_size_result_defaults_optional_shared_fields() -> None:
    result = DesignSampleSizeResult(
        metric_family="continuous_mean",
        group_sample_sizes={"control": 100, "treatment_1": 100},
        overall_total=200,
    )

    assert result.metric_family == "continuous_mean"
    assert result.per_comparison_total is None
    assert result.alpha is None
    assert result.adjusted_alpha is None
    assert result.comparisons == 1
