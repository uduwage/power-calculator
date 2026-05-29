from power_calculator.core.base import MetricFamilyDesignCalculator
from power_calculator.core.models import (
    BinaryDesignInputs,
    DesignRequest,
    DesignSampleSizeResult,
    ExperimentDesignSettings,
)


class ExampleBinaryDesignCalculator:
    """Minimal example implementation of the shared design contract."""

    def calculate_sample_size(
        self,
        request: DesignRequest[BinaryDesignInputs],
    ) -> DesignSampleSizeResult:
        return DesignSampleSizeResult(
            metric_family=request.metric_family,
            group_sample_sizes={"control": 100, "treatment_1": 100},
            overall_total=200,
            per_comparison_total=200,
            comparisons=1,
        )


def test_metric_family_design_calculator_protocol_accepts_example() -> None:
    calculator = ExampleBinaryDesignCalculator()
    request = DesignRequest(
        metric_family="binary",
        settings=ExperimentDesignSettings(),
        inputs=BinaryDesignInputs(),
    )

    assert isinstance(calculator, MetricFamilyDesignCalculator)
    result = calculator.calculate_sample_size(request)

    assert result.metric_family == "binary"
    assert result.group_sample_sizes == {"control": 100, "treatment_1": 100}
    assert result.overall_total == 200
