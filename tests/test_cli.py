from power_calculator.cli import main


def test_cli_50_50_current_behavior(capsys) -> None:
    exit_code = main(
        [
            "--alternative",
            "two-sided",
            "--confidence",
            "95",
            "--power",
            "80",
            "--groups",
            "2",
            "--baseline-rate",
            "10",
            "--mde",
            "2",
            "--allocation",
            "50:50",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Binary A/B(/n) Sample Size" in captured.out
    assert "Allocation (control:treatment): 50.00%:50.00%" in captured.out
    assert "Overall total sample size across all groups: 7,682" in captured.out
    assert captured.err == ""


def test_cli_groups_gt_2_explicit_allocation(capsys) -> None:
    exit_code = main(
        [
            "--alternative",
            "two-sided",
            "--confidence",
            "95",
            "--power",
            "80",
            "--groups",
            "4",
            "--baseline-rate",
            "10",
            "--mde",
            "2",
            "--allocation",
            "40:60:60:60",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Groups: 4" in captured.out
    assert "Comparisons: 3" in captured.out
    assert "Allocation (control:treatment): 40.00%:60.00%" in captured.out
    assert "Overall total sample size across all groups: 17,523" in captured.out
    assert captured.err == ""


def test_cli_rejects_two_part_allocation_for_groups_gt_2(capsys) -> None:
    exit_code = main(
        [
            "--groups",
            "3",
            "--baseline-rate",
            "10",
            "--mde",
            "2",
            "--allocation",
            "50:50",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "power-calculator: error: Allocation has 2 values but groups=3." in captured.err
    )


def test_cli_rejects_three_part_allocation_for_two_groups(capsys) -> None:
    exit_code = main(
        [
            "--groups",
            "2",
            "--baseline-rate",
            "10",
            "--mde",
            "2",
            "--allocation",
            "33:33:34",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "power-calculator: error: Allocation has 3 values but groups=2." in captured.err
    )


def test_cli_prints_duration_estimate_when_daily_users_provided(capsys) -> None:
    exit_code = main(
        [
            "--groups",
            "2",
            "--baseline-rate",
            "10",
            "--mde",
            "2",
            "--allocation",
            "50:50",
            "--daily-users",
            "5000",
            "--eligible-rate",
            "90",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Duration Estimate" in captured.out
    assert "Daily users: 5,000.00" in captured.out
    assert "Eligible rate: 90.00%" in captured.out
    assert "Expected daily eligible users: 4,500.00" in captured.out
    assert "Estimated duration:" in captured.out
    assert "Bottleneck group:" in captured.out
    assert captured.err == ""


def test_cli_rejects_eligible_rate_without_daily_users(capsys) -> None:
    exit_code = main(
        [
            "--groups",
            "2",
            "--baseline-rate",
            "10",
            "--mde",
            "2",
            "--allocation",
            "50:50",
            "--eligible-rate",
            "90",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "power-calculator: error: --eligible-rate requires --daily-users."
        in captured.err
    )
