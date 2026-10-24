"""Tests for held-out selection and conservative escalation semantics."""

from scripts.validate_adequacy_policy import classify, score, select_policy


def row(
    accurate: bool, rmse: float, lag: float, status: str = "REVIEW_REQUIRED"
) -> dict[str, object]:
    return {
        "centers_within_tolerance": accurate,
        "normalized_rmse": rmse,
        "abs_lag1": lag,
        "current_status": status,
    }


def test_accepted_cases_never_escalated_by_experimental_policy() -> None:
    assert classify(row(False, 0.9, 0.99, "FIT_OK"), 0.1, 0.8) == "FIT_OK"


def test_both_gates_required_for_failure() -> None:
    assert classify(row(False, 0.2, 0.99), 0.1, 0.8) == "FIT_FAILED"
    assert classify(row(False, 0.05, 0.99), 0.1, 0.8) == "REVIEW_REQUIRED"


def test_scoring_review_as_abstention() -> None:
    cases = [row(True, 0.01, 0.1), row(False, 0.2, 0.99), row(False, 0.2, 0.99)]
    results = score(cases, ["REVIEW_REQUIRED", "FIT_FAILED", "FIT_OK"])
    assert results["failure_recall"] == 0.5
    assert results["false_accept_rate"] == 0.5
    assert results["false_failure_rate"] == 0


def test_selection_uses_constraint() -> None:
    cases = [
        row(True, 0.01, 0.1),
        row(True, 0.08, 0.99),
        row(False, 0.19, 0.99),
    ]
    rmse, lag = select_policy(cases, max_false_failure=0)
    statuses = [classify(case, rmse, lag) for case in cases]
    assert statuses[1] != "FIT_FAILED"
    assert statuses[2] == "FIT_FAILED"
