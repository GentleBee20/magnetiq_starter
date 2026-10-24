"""Evidence catalogue for provisional ODMR fit diagnostics.

Stage labels describe where to investigate, not proven root causes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactExplanation:
    code: str
    category: str
    investigation_stage: str
    interpretation: str
    next_check: str


CATALOGUE: dict[str, ArtifactExplanation] = {
    "optimization_failed": ArtifactExplanation(
        "optimization_failed", "model_fit", "fitting",
        "No candidate fit converged reliably.", "Inspect input values and optimizer diagnostics.",
    ),
    "high_relative_residual": ArtifactExplanation(
        "high_relative_residual", "model_mismatch", "signal_evaluation",
        "Residual size exceeds the provisional relative threshold.",
        "Inspect spectrum and model overlay; compare alternative line shapes.",
    ),
    "structured_residuals": ArtifactExplanation(
        "structured_residuals", "structured_residual", "signal_evaluation",
        "Adjacent residual samples are strongly correlated.",
        "Inspect residual structure; test drift or oscillatory contamination.",
    ),
    "ambiguous_model_selection": ArtifactExplanation(
        "ambiguous_model_selection", "model_ambiguity", "fitting",
        "Competing converged fit models have similar AICc.",
        "Review both fits; do not overinterpret model identity.",
    ),
    "no_resonance_selected": ArtifactExplanation(
        "no_resonance_selected", "model_ambiguity", "fitting",
        "The selected baseline model contains no fitted resonance.",
        "Check signal contrast, acquisition range and fit candidates.",
    ),
    "linewidth_near_constraint": ArtifactExplanation(
        "linewidth_near_constraint", "parameter_boundary", "fitting",
        "A fitted linewidth is near the resolution or span constraints.",
        "Check frequency sampling and alternate fitting bounds.",
    ),
    "center_near_edge": ArtifactExplanation(
        "center_near_edge", "parameter_boundary", "acquisition_or_fitting",
        "A resonance center is near the measured frequency boundary.",
        "Check sweep coverage before interpreting this parameter.",
    ),
    "weak_resonance": ArtifactExplanation(
        "weak_resonance", "low_contrast", "acquisition_or_fitting",
        "The fitted resonance has weak contrast against observed signal variation.",
        "Inspect noise, contrast and raw acquisition settings.",
    ),
    "local_residual_unassessable": ArtifactExplanation(
        "local_residual_unassessable", "insufficient_reference", "signal_evaluation",
        "Insufficient quiet residual region to assess local errors.",
        "Review measurement bandwidth and usable off-resonance region.",
    ),
    "resonance_local_residual_excess": ArtifactExplanation(
        "resonance_local_residual_excess", "local_model_mismatch", "signal_evaluation",
        "Residual energy is elevated around a fitted resonance.",
        "Inspect local residual shape and candidate line shape.",
    ),
    "resonance_local_bias": ArtifactExplanation(
        "resonance_local_bias", "local_model_mismatch", "signal_evaluation",
        "A local signed residual offset is elevated near resonance.",
        "Check systematic offsets and model adequacy near the dip.",
    ),
    "unresolved_resonances": ArtifactExplanation(
        "unresolved_resonances", "resolution_limit", "acquisition_or_fitting",
        "Fitted centers are poorly separated relative to frequency resolution.",
        "Review sweep resolution and identifiability.",
    ),
}


def describe_warnings(codes: tuple[str, ...]) -> list[dict[str, str]]:
    """Preserve unknown codes and never manufacture physical diagnoses."""
    descriptions: list[dict[str, str]] = []
    for code in codes:
        match = CATALOGUE.get(code)
        if match is None:
            descriptions.append({
                "code": code, "category": "unclassified",
                "investigation_stage": "undetermined",
                "interpretation": "No curated explanation for this diagnostic code.",
                "next_check": "Review the source diagnostic implementation.",
            })
        else:
            descriptions.append({
                "code": match.code, "category": match.category,
                "investigation_stage": match.investigation_stage,
                "interpretation": match.interpretation, "next_check": match.next_check,
            })
    return descriptions
