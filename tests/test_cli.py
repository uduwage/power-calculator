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

def test_cli_groups_gt_2_40_60_current_behavior(capsys) -> None:
    exit_code = main(
        [
            "--alternative",
            "two-sided",
            "--confidence",
            "95",
            "--power",
            "80",
            "groups",
            "4",
            "--baseline-rate",
            "10",
            "--mde",
            "2",
            "--allocation",
            "40:60",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Groups: 4" in captured.out
    assert "Comparisons: 3" in captured.out
    assert "Allocation (control:treatment): 40.00%:60.00%" in captured.out
    assert "Overall total sample size across all groups: 17,523" in captured.out
    assert captured.err == ""

def test_cli_rejects_three_part_allocation_today(capsys) -> None:
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
        "power-calculator: error: Allocation must be in 'control:treatment' format "
        "(e.g. 50:50)."
    ) in captured.err    