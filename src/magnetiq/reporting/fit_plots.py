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
    figure, (axis, residual_axis) = plt.subplots(
        2, 1, figsize=(10, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
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
