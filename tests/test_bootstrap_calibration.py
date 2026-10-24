"""Bootstrap calibration coverage summary checks."""

from scripts.benchmark_bootstrap_calibration import summarize


def test_marginal_and_joint_coverage_are_distinct() -> None:
    rows: list[dict[str, object]] = [
        {"assessable": True, "covered_1": True, "covered_2": False, "joint_covered": False},
        {"assessable": True, "covered_1": True, "covered_2": True, "joint_covered": True},
        {"assessable": False, "covered_1": None, "covered_2": None, "joint_covered": None},
    ]
    metrics = summarize(rows)
    assert metrics["assessable"] == 2
    assert metrics["coverage_center_1"] == 1
    assert metrics["coverage_center_2"] == 0.5
    assert metrics["joint_coverage"] == 0.5
