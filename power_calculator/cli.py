"""CLI entrypoint for the power-calculator package.

Notes:
    Parses command-line arguments, validates inputs, runs sample-size
    calculations, and optionally prints duration estimates.
"""

from __future__ import annotations

import argparse
import sys

from power_calculator.core.allocation import _parse_allocation
from power_calculator.core.binary import BinaryDesignCalculator
from power_calculator.core.models import (
    BinaryDesignInputs,
    DesignRequest,
    DesignSampleSizeResult,
    ExperimentDesignSettings,
)
from power_calculator.duration import estimate_duration_by_group


def _to_probability(value: float, flag_name: str, allow_one: bool = False) -> float:
    """Normalize probability-like CLI input to 0-1 scale.

    Args:
        value: Input value, either in 0-1 scale or 0-100 percent.
        flag_name: Flag name for validation error messages.
        allow_one: If true, accepts `1.0`/`100` as valid upper bound and
            validates against `(0, 1]`; otherwise validates against `(0, 1)`.

    Returns:
        Normalized probability value in 0-1 scale.

    Raises:
        ValueError: If value falls outside the allowed open/closed interval.
    """
    if value > 1:
        value = value / 100.0
    if allow_one:
        if not (0 < value <= 1):
            raise ValueError(
                f"{flag_name} must be in (0, 1] " "(or percent form, allowing 100)."
            )
    elif not (0 < value < 1):
        raise ValueError(
            f"{flag_name} must be in (0, 1) " "(or percent form, excluding 0 and 100)."
        )
    return value


def _build_binary_design_request(
    args: argparse.Namespace,
    confidence_level: float,
    power: float,
) -> DesignRequest[BinaryDesignInputs]:
    """Build the shared binary design request used by the CLI."""
    return DesignRequest(
        metric_family="binary",
        settings=ExperimentDesignSettings(
            alternative=args.alternative,
            confidence_level=confidence_level,
            power=power,
            groups=args.groups,
            correction=args.correction,
            allocation=args.allocation,
        ),
        inputs=BinaryDesignInputs(
            baseline_rate_pct=args.baseline_rate,
            mde_pct=args.mde,
        ),
    )


def _get_pairwise_binary_allocation(
    allocation_shares: list[float],
) -> tuple[float, float]:
    """Return pairwise control and treatment allocations for CLI display."""
    control_share = allocation_shares[0]
    first_treatment_share = allocation_shares[1]
    pair_total = control_share + first_treatment_share
    return control_share / pair_total, first_treatment_share / pair_total


def _get_required_binary_cli_result_fields(
    result: DesignSampleSizeResult,
) -> tuple[float, float, int]:
    """Return the non-optional shared result fields required by the binary CLI."""
    if result.alpha is None:
        raise ValueError("Binary design calculator returned no raw alpha.")
    if result.adjusted_alpha is None:
        raise ValueError("Binary design calculator returned no adjusted alpha.")
    if result.per_comparison_total is None:
        raise ValueError("Binary design calculator returned no per-comparison total.")
    return result.alpha, result.adjusted_alpha, result.per_comparison_total


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser.

    Returns:
        Configured argument parser for the power calculator CLI.
    """
    parser = argparse.ArgumentParser(
        prog="power-calculator",
        description="Binary metric sample size calculator for A/B(/n) tests.",
    )
    parser.add_argument(
        "--alternative",
        choices=["one-sided", "two-sided"],
        default="two-sided",
        help="Alternative hypothesis type.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=95.0,
        help="Confidence level (1-alpha). Accepts 95 or 0.95.",
    )
    parser.add_argument(
        "--power",
        type=float,
        default=80.0,
        help="Statistical power (1-beta). Accepts 80 or 0.8.",
    )
    parser.add_argument(
        "--groups",
        type=int,
        default=2,
        help="Total number of groups, including control.",
    )
    parser.add_argument(
        "--correction",
        choices=["none", "bonferroni", "sidak"],
        default="none",
        help="Multiple testing correction for multi-group tests.",
    )
    parser.add_argument(
        "--baseline-rate",
        type=float,
        required=True,
        help="Baseline binary metric rate in percentage (e.g. 10 for 10%%).",
    )
    parser.add_argument(
        "--mde",
        type=float,
        required=True,
        help="Minimum detectable effect in percentage points (Y_t - Y_c).",
    )
    parser.add_argument(
        "--allocation",
        default="50:50",
        help=(
            "Allocation ratio between groups. "
            "Default is '50:50' for --groups 2 (control:treatment). "
            "For --groups > 2, pass an explicit allocation with exactly --groups "
            "values in control:t1:t2:... form (e.g. '50:25:25' for --groups 3); "
            "'50:50' is invalid in that case."
        ),
    )
    parser.add_argument(
        "--daily-users",
        type=float,
        default=None,
        help="Average daily users available for the experiment.",
    )
    parser.add_argument(
        "--eligible-rate",
        type=float,
        default=1.0,
        help=(
            "Share of daily users eligible for the test. "
            "Accepts 0-1 or 0-100 input. "
            "Default: 1.0 (100%%)."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entrypoint.

    Args:
        argv: Optional explicit CLI args. Uses `sys.argv` when omitted.

    Returns:
        Exit code (`0` for success, `2` for validation failures).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        confidence = _to_probability(args.confidence, "--confidence")
        power = _to_probability(args.power, "--power")
        eligible_rate = _to_probability(
            args.eligible_rate, "--eligible-rate", allow_one=True
        )
        request = _build_binary_design_request(args, confidence, power)
        calculator = BinaryDesignCalculator()
        result = calculator.calculate_sample_size(request)
        raw_alpha, adjusted_alpha, per_comparison_total = (
            _get_required_binary_cli_result_fields(result)
        )
        allocation_shares = _parse_allocation(
            request.settings.allocation, request.settings.groups
        )
        control_allocation, treatment_allocation = _get_pairwise_binary_allocation(
            allocation_shares
        )
        baseline_rate = request.inputs.baseline_rate_pct / 100.0
        minimum_detectable_effect = request.inputs.mde_pct / 100.0
        variant_rate = baseline_rate + minimum_detectable_effect
        control_sample_size = result.group_sample_sizes["control"]
        treatment_sample_size = result.group_sample_sizes["treatment_1"]
        duration = None
        if args.daily_users is not None:
            if args.daily_users <= 0:
                raise ValueError("--daily-users must be positive.")
            traffic_shares = {"control": allocation_shares[0]}
            for idx, traffic_share in enumerate(allocation_shares[1:], start=1):
                traffic_shares[f"treatment_{idx}"] = traffic_share

            duration = estimate_duration_by_group(
                group_sample_sizes=result.group_sample_sizes,
                daily_users=args.daily_users,
                traffic_shares=traffic_shares,
                eligible_rate=eligible_rate,
            )
        elif eligible_rate != 1.0:
            raise ValueError("--eligible-rate requires --daily-users.")
    except ValueError as exc:
        print(f"{parser.prog}: error: {exc}", file=sys.stderr)
        return 2

    print("Binary A/B(/n) Sample Size")
    print(f"Alternative hypothesis: {args.alternative}")
    print(f"Confidence level (1-alpha): {confidence:.2%}")
    print(f"Power (1-beta): {power:.2%}")
    print(f"Groups: {args.groups}")
    print(f"Multiple testing correction: {args.correction}")
    print(f"Raw alpha: {raw_alpha:.4f}")
    print(f"Adjusted alpha: {adjusted_alpha:.4f}")
    print(f"Comparisons: {result.comparisons}")
    print(
        f"Allocation (control:treatment): "
        f"{control_allocation:.2%}:{treatment_allocation:.2%}"
    )
    print(f"Baseline rate: {baseline_rate:.2%}")
    print(f"MDE: {minimum_detectable_effect:.2%}")
    print(f"Implied treatment rate: {variant_rate:.2%}")
    print()
    print(f"Required control sample size: {control_sample_size:,}")
    print(f"Required sample size per treatment group: {treatment_sample_size:,}")
    print(f"Total per control-vs-treatment comparison: {per_comparison_total:,}")
    print(f"Overall total sample size across all groups: {result.overall_total:,}")
    if duration is not None:
        print()
        print("Duration Estimate")
        print(f"Daily users: {args.daily_users:,.2f}")
        eligible_pct = duration.expected_daily_eligible_users / args.daily_users
        print(f"Eligible rate: {eligible_pct:.2%}")
        expected_daily = duration.expected_daily_eligible_users
        print(f"Expected daily eligible users: {expected_daily:,.2f}")
        print(f"Estimated duration: {duration.days_required} day(s)")
        bottleneck_group = max(
            duration.days_per_group, key=lambda group: duration.days_per_group[group]
        )  # fixing annoying mypy typing error
        bottleneck_days = duration.days_per_group[bottleneck_group]
        print(f"Bottleneck group: {bottleneck_group} ({bottleneck_days} days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
