"""Candidate model-adequacy policy; NOT used for production fit statuses.

Thresholds are exploratory and must be benchmarked with labelled/reference data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from magnetiq.processing.diagnostics import FitDiagnostics


@dataclass(frozen=True)
class AdequacyAssessment:
    """Explain why the experimental severe-mismatch gate does or does not fire."""

    candidate_status: str
    severe_reasons: tuple[str, ...]
    needs_review: bool


def assess_candidate(diagnosis: FitDiagnostics) -> AdequacyAssessment:
    """Apply an exploratory severe-mismatch gate without mutating current QC.

    A severe decision requires global residual magnitude AND other independent
    evidence. Local warnings alone never imply a failed fit.
    """
    if diagnosis.status == "FIT_FAILED":
        return AdequacyAssessment("FIT_FAILED", ("optimization_failed",), False)

    reasons: list[str] = []
    if np.isfinite(diagnosis.normalized_rmse) and diagnosis.normalized_rmse > 0.20:
        reasons.append("severe_global_relative_rmse")
    if diagnosis.max_local_rmse_ratio is not None and diagnosis.max_local_rmse_ratio > 4.0:
        reasons.append("severe_resonance_local_mismatch")
    if (
        np.isfinite(diagnosis.lag1_residual_correlation)
        and abs(diagnosis.lag1_residual_correlation) > 0.8
    ):
        reasons.append("severe_residual_structure")

    # Both broad inadequacy AND corroboration are needed for a candidate failure.
    severe = "severe_global_relative_rmse" in reasons and len(reasons) >= 2
    status = (
        "FIT_FAILED"
        if severe
        else ("REVIEW_REQUIRED" if diagnosis.status != "FIT_OK" or reasons else "FIT_OK")
    )
    return AdequacyAssessment(status, tuple(reasons), status == "REVIEW_REQUIRED")
