"""Ground-truth synthetic benchmark invariants."""

import numpy as np

from scripts.benchmark_ground_truth import evaluate, make_cases, performance


def test_seeded_generation_is_reproducible() -> None:
    first = make_cases(42, 1)
    second = make_cases(42, 1)
    assert len(first) == 16
    for a, b in zip(first, second):
        assert a[:3] == b[:3]
        assert np.array_equal(a[3], b[3])
        assert np.array_equal(a[4], b[4])


def test_center_error_uses_both_known_centers() -> None:
    rows = evaluate(make_cases(8, 1)[:1], tolerance_mhz=0.5)
    assert len(rows) == 1
    assert rows[0]["distortion"] == "clean"
    assert rows[0]["max_center_error_mhz"] >= 0
    assert rows[0]["center_truth_1_ghz"] < rows[0]["center_truth_2_ghz"]


def test_performance_denominators_include_unresolved_cases() -> None:
    rows = [
        {"centers_within_tolerance": True, "current_status": "FIT_OK"},
        {"centers_within_tolerance": False, "current_status": "FIT_OK"},
        {"centers_within_tolerance": False, "current_status": "REVIEW_REQUIRED"},
    ]
    metrics = performance(rows, "current_status")
    assert metrics["false_accept_given_inaccurate"] == 0.5
    assert metrics["accept_rate"] == 2 / 3
