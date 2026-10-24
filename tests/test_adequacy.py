"""Candidate classification gate tests (independent from production status)."""

from dataclasses import replace

from magnetiq.processing.adequacy import assess_candidate
from magnetiq.processing.diagnostics import FitDiagnostics


def diagnostic(**changes: object) -> FitDiagnostics:
    baseline = FitDiagnostics(
        "synthetic",
        "double",
        "FIT_OK",
        (),
        0.001,
        0.03,
        0.002,
        0.2,
        12.0,
        2.866,
        2.875,
        9.0,
        1.0,
        1.0,
        0.02,
        0.03,
    )
    return replace(baseline, **changes)


def test_strong_local_mismatch_alone_is_review_not_failure() -> None:
    result = assess_candidate(diagnostic(max_local_rmse_ratio=6.0))
    assert result.candidate_status == "REVIEW_REQUIRED"


def test_global_mismatch_requires_corroboration() -> None:
    result = assess_candidate(diagnostic(normalized_rmse=0.25))
    assert result.candidate_status == "REVIEW_REQUIRED"


def test_severe_global_error_plus_structure_is_candidate_failure() -> None:
    result = assess_candidate(diagnostic(normalized_rmse=0.25, lag1_residual_correlation=0.93))
    assert result.candidate_status == "FIT_FAILED"


def test_existing_optimization_failure_is_preserved() -> None:
    result = assess_candidate(diagnostic(status="FIT_FAILED"))
    assert result.candidate_status == "FIT_FAILED"
