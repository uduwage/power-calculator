"""CLI for the power-calculator package."""

from __future__ import annotations

import argparse
import sys

from power_calculator.binary_power import SampleSizeInput, calculate_sample_size
from power_calculator.duration import estimate_duration_by_group


def _to_probability(value: float, flag_name: str, allow_one: bool = False) -> float:
    """Normalize probability-like CLI input to 0-1 scale.

    Args:
        value: Input value, either in 0-1 scale or 0-100 percent.
        flag_name: Flag name for validation error messages.
        allow_one: If true, accepts `1.0`/`100` as valid upper bound.

    Returns:
        Normalized probability value in 0-1 scale.

    Raises:
        ValueError: If value falls outside the allowed range.
    """
    if value > 1:
        value = value / 100.0
    if allow_one:
        if not (0 < value <= 1):
            raise ValueError(
                f"{flag_name} must be > 0 and <= 1 (or 0 and 100 as percentage, allowing 100)."
            )
    elif not (0 < value < 1):
        raise ValueError(f"{flag_name} must be between 0 and 1 (or 0 and 100 as percentage).")
    return value


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
        help="Control:treatment allocation ratio. Default is 50:50.",
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
        default=100.0,
        help=(
            "Share of daily users eligible for the test. "
            "Accepts 100 or 1.0 for 100%%."
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
        config = SampleSizeInput(
            alternative=args.alternative,
            confidence_level=confidence,
            power=power,
            groups=args.groups,
            correction=args.correction,
            baseline_rate_pct=args.baseline_rate,
            mde_pct=args.mde,
            allocation=args.allocation,
        )
        result = calculate_sample_size(config)
        duration = None
        if args.daily_users is not None:
            if args.daily_users <= 0:
                raise ValueError("--daily-users must be positive.")
            eligible_rate = _to_probability(args.eligible_rate, "--eligible-rate", allow_one=True)
            group_sample_sizes = {"control": result.control_sample_size}
            for idx in range(1, args.groups):
                group_sample_sizes[f"treatment_{idx}"] = result.treatment_sample_size

            total_weight = result.control_allocation + (
                (args.groups - 1) * result.treatment_allocation
            )
            control_share = result.control_allocation / total_weight
            treatment_share = result.treatment_allocation / total_weight

            traffic_shares = {"control": control_share}
            for idx in range(1, args.groups):
                traffic_shares[f"treatment_{idx}"] = treatment_share

            duration = estimate_duration_by_group(
                group_sample_sizes=group_sample_sizes,
                daily_users=args.daily_users,
                traffic_shares=traffic_shares,
                eligible_rate=eligible_rate,
            )
        elif args.eligible_rate != 100.0:
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
    print(f"Raw alpha: {result.alpha:.4f}")
    print(f"Adjusted alpha: {result.adjusted_alpha:.4f}")
    print(f"Comparisons: {result.comparisons}")
    print(
        f"Allocation (control:treatment): "
        f"{result.control_allocation:.2%}:{result.treatment_allocation:.2%}"
    )
    print(f"Baseline rate: {result.baseline_rate:.2%}")
    print(f"MDE: {result.mde:.2%}")
    print(f"Implied treatment rate: {result.variant_rate:.2%}")
    print()
    print(f"Required control sample size: {result.control_sample_size:,}")
    print(f"Required sample size per treatment group: {result.treatment_sample_size:,}")
    print(f"Total per control-vs-treatment comparison: {result.per_comparison_total:,}")
    print(f"Overall total sample size across all groups: {result.overall_total:,}")
    if duration is not None:
        print()
        print("Duration Estimate")
        print(f"Daily users: {args.daily_users:,.2f}")
        print(f"Eligible rate: {duration.expected_daily_eligible_users / args.daily_users:.2%}")
        print(f"Expected daily eligible users: {duration.expected_daily_eligible_users:,.2f}")
        print(f"Estimated duration: {duration.days_required} day(s)")
        bottleneck_group = max(duration.days_per_group, key=duration.days_per_group.get)
        print(f"Bottleneck group: {bottleneck_group} ({duration.days_per_group[bottleneck_group]} days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
