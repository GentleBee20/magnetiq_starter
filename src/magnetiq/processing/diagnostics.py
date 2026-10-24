"""Exploratory fit diagnostics, not sensor calibration or device fault labels."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.resonance import ResonanceFit, evaluate_model

MODEL_PEAKS = {"baseline": 0, "single": 1, "double": 2}


@dataclass(frozen=True)
class FitDiagnostics:
    """Evidence-backed warnings about fit quality, not physical accuracy."""

    source: str
    model: str
    status: str
    warnings: tuple[str, ...]
    rmse: float
    normalized_rmse: float
    max_abs_residual: float
    lag1_residual_correlation: float
    delta_aicc_to_runner_up: float
    center_1_ghz: float | None
    center_2_ghz: float | None
    separation_mhz: float | None
    width_1_mhz: float | None
    width_2_mhz: float | None
    amplitude_1: float | None
    amplitude_2: float | None


def choose_fit(fits: list[ResonanceFit]) -> ResonanceFit:
    """Select minimum finite AICc among converged candidates."""
    eligible = [fit for fit in fits if fit.success and np.isfinite(fit.aicc)]
    return min(eligible, key=lambda fit: fit.aicc) if eligible else fits[0]


def diagnose_fit(spectrum: OdmrSpectrum, fits: list[ResonanceFit]) -> FitDiagnostics:
    """Compute transparent, provisional thresholds for internal fit review."""
    if not fits:
        raise ValueError("At least one candidate fit is required")
    fit = choose_fit(fits)
    eligible = sorted(
        (candidate for candidate in fits if candidate.success and np.isfinite(candidate.aicc)),
        key=lambda candidate: candidate.aicc,
    )
    delta = eligible[1].aicc - eligible[0].aicc if len(eligible) > 1 else float("nan")
    if not fit.success or not fit.parameters:
        return FitDiagnostics(
            spectrum.source,
            fit.model,
            "FIT_FAILED",
            ("optimization_failed",),
            float("nan"),
            float("nan"),
            float("nan"),
            float("nan"),
            delta,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
    frequency = np.asarray(spectrum.frequency_ghz, dtype=float)
    measured = np.asarray(spectrum.normalized_contrast, dtype=float)
    prediction = evaluate_model(frequency, np.asarray(fit.parameters), MODEL_PEAKS[fit.model])
    residual = measured - prediction
    signal_range = float(np.ptp(measured))
    normalized = fit.rmse / signal_range if signal_range > 0 else float("inf")
    lag1 = float("nan")
    if len(residual) > 2 and float(np.std(residual[:-1])) > 0 and float(np.std(residual[1:])) > 0:
        lag1 = float(np.corrcoef(residual[:-1], residual[1:])[0, 1])

    warnings: list[str] = []
    # Heuristics only: thresholds require calibration against labelled experiments.
    if not np.isfinite(normalized) or normalized > 0.15:
        warnings.append("high_relative_residual")
    if np.isfinite(lag1) and abs(lag1) > 0.7:
        warnings.append("structured_residuals")
    if len(eligible) > 1 and delta < 2:
        warnings.append("ambiguous_model_selection")

    peaks = MODEL_PEAKS[fit.model]
    peak_params = [
        (
            fit.parameters[2 + 3 * index],
            fit.parameters[3 + 3 * index],
            fit.parameters[4 + 3 * index],
        )
        for index in range(peaks)
    ]
    spacing = float(np.median(np.diff(frequency)))
    span = float(np.ptp(frequency))
    if peaks == 0:
        warnings.append("no_resonance_selected")
    for amplitude, center, width in peak_params:
        if width <= spacing / 3 or width >= 0.48 * span:
            warnings.append("linewidth_near_constraint")
        if center <= frequency[0] + spacing or center >= frequency[-1] - spacing:
            warnings.append("center_near_edge")
        if amplitude <= 0.01 * max(signal_range, 1e-12):
            warnings.append("weak_resonance")
    if peaks == 2:
        separation = abs(peak_params[1][1] - peak_params[0][1]) * 1000
        if separation <= 2 * spacing * 1000:
            warnings.append("unresolved_resonances")
    else:
        separation = None

    def field(index: int, item: int, scale: float = 1.0) -> float | None:
        return float(peak_params[index][item] * scale) if len(peak_params) > index else None

    return FitDiagnostics(
        spectrum.source,
        fit.model,
        "REVIEW_REQUIRED" if warnings else "FIT_OK",
        tuple(dict.fromkeys(warnings)),
        fit.rmse,
        normalized,
        float(np.max(np.abs(residual))),
        lag1,
        delta,
        field(0, 1),
        field(1, 1),
        separation,
        field(0, 2, 1000),
        field(1, 2, 1000),
        field(0, 0),
        field(1, 0),
    )
