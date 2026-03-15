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