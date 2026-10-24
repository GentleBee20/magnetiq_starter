"""Scientific plots of fitted ODMR spectra and residual diagnostics."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.diagnostics import MODEL_PEAKS, FitDiagnostics
from magnetiq.processing.resonance import ResonanceFit, evaluate_model


def plot_fit(
    spectrum: OdmrSpectrum, fit: ResonanceFit, diagnosis: FitDiagnostics, output: Path
) -> None:
    """Save overlay and frequency-dependent residual figure."""
    frequency = np.asarray(spectrum.frequency_ghz)
    measured = np.asarray(spectrum.normalized_contrast)
    figure = plt.figure(figsize=(11, 9))
    grid = figure.add_gridspec(3, 1, height_ratios=[3, 1, 1.8])
    axis = figure.add_subplot(grid[0])
    residual_axis = figure.add_subplot(grid[1], sharex=axis)
    diagnostics_axis = figure.add_subplot(grid[2])
    diagnostics_axis.axis("off")
    axis.plot(frequency, measured, ".", markersize=2, alpha=0.65, label="Measured contrast")
    if fit.success and fit.parameters:
        prediction = evaluate_model(frequency, np.asarray(fit.parameters), MODEL_PEAKS[fit.model])
        axis.plot(frequency, prediction, linewidth=1.5, label=f"{fit.model} fit")
        for center in (diagnosis.center_1_ghz, diagnosis.center_2_ghz):
            if center is not None:
                axis.axvline(center, linestyle=":", linewidth=0.8, color="gray")
        residual_axis.plot(frequency, measured - prediction, linewidth=0.9)
        for center, width_mhz in (
            (diagnosis.center_1_ghz, diagnosis.width_1_mhz),
            (diagnosis.center_2_ghz, diagnosis.width_2_mhz),
        ):
            if center is not None and width_mhz is not None:
                half_width = 2 * width_mhz / 1000
                residual_axis.axvspan(
                    center - half_width, center + half_width, color="orange", alpha=0.12
                )
    else:
        residual_axis.text(0.5, 0.5, "Fit failed", transform=residual_axis.transAxes, ha="center")
    residual_axis.axhline(0, color="black", linewidth=0.7)
    axis.set_ylabel("Normalized contrast")
    axis.legend(loc="best")
    axis.set_title(f"{Path(spectrum.source).name} | {diagnosis.status}")
    residual_axis.set_ylabel("Residual")
    residual_axis.set_xlabel("Microwave frequency (GHz)")
    diagnostics_axis.text(
        0.0,
        0.98,
        f"FIT QUALITY: {diagnosis.status} | Model: {diagnosis.model}",
        transform=diagnostics_axis.transAxes,
        va="top",
        fontsize=11,
        fontweight="bold",
    )
    reasons = ", ".join(diagnosis.warnings) if diagnosis.warnings else "No heuristic warnings"
    report_lines = [
        f"Warnings: {reasons}",
        f"RMSE: {diagnosis.rmse:.4g} | Relative RMSE: {diagnosis.normalized_rmse:.3g} (limit 0.15)",
        f"|Lag-1 residual correlation|: {abs(diagnosis.lag1_residual_correlation):.3g} (limit 0.7)",
        f"Local RMSE / off-res noise: R1={diagnosis.resonance_1_local_rmse_ratio}, "
        f"R2={diagnosis.resonance_2_local_rmse_ratio} (limit 2)",
        f"Local bias / off-res noise: R1={diagnosis.resonance_1_local_bias_ratio}, "
        f"R2={diagnosis.resonance_2_local_bias_ratio} (limit 1)",
        "Orange shading: +/- 2 fitted Lorentzian half-widths at each resonance",
        "Status is provisional fitting QC; NOT a calibrated measurement or hardware verdict.",
    ]
    diagnostics_axis.text(
        0.0, 0.81, "\\n".join(report_lines), transform=diagnostics_axis.transAxes,
        va="top", fontsize=8.5, linespacing=1.45,
    )
    figure.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=160)
    plt.close(figure)


def plot_batch(diagnostics: list[FitDiagnostics], output: Path) -> None:
    """Save a batch overview of normalized residuals and review categories."""
    valid = [diagnosis for diagnosis in diagnostics if np.isfinite(diagnosis.normalized_rmse)]
    labels = ["FIT_OK", "REVIEW_REQUIRED", "FIT_FAILED"]
    counts = [sum(diagnosis.status == label for diagnosis in diagnostics) for label in labels]
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    if valid:
        axes[0].hist(
            [diagnosis.normalized_rmse for diagnosis in valid], bins=min(15, max(3, len(valid)))
        )
    axes[0].set_xlabel("RMSE / observed contrast range")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Relative residual magnitude")
    axes[1].bar(labels, counts)
    axes[1].set_ylabel("Count")
    axes[1].set_title("Provisional fit statuses")
    axes[1].tick_params(axis="x", labelrotation=18)
    figure.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=160)
    plt.close(figure)
