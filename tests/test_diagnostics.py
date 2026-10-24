"""Tests for fit diagnostics and rendering without external experimental data."""

from pathlib import Path

import numpy as np

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.diagnostics import choose_fit, diagnose_fit
from magnetiq.processing.resonance import ResonanceFit, evaluate_model, fit_spectrum
from magnetiq.reporting.fit_plots import plot_batch, plot_fit


def test_synthetic_two_peak_diagnostics(tmp_path: Path) -> None:
    frequency = np.linspace(2.85, 2.89, 401)
    parameters = np.array([1.0, 0.0, 0.04, 2.866, 0.0012, 0.03, 2.875, 0.0015])
    contrast = evaluate_model(frequency, parameters, 2)
    spectrum = OdmrSpectrum("synthetic", tuple(frequency), tuple(contrast))
    fits = [fit_spectrum(spectrum, n) for n in (0, 1, 2)]
    diagnostics = diagnose_fit(spectrum, fits)
    assert diagnostics.model == "double"
    assert diagnostics.status in {"FIT_OK", "REVIEW_REQUIRED"}
    assert diagnostics.separation_mhz is not None
    assert abs(diagnostics.separation_mhz - 9) < 1
    plot_fit(spectrum, choose_fit(fits), diagnostics, tmp_path / "fit.png")
    plot_batch([diagnostics], tmp_path / "summary.png")
    assert (tmp_path / "fit.png").exists()
    assert (tmp_path / "summary.png").exists()


def test_failed_fit_is_reported() -> None:
    spectrum = OdmrSpectrum("short", (2.85, 2.86), (1.0, 0.9))
    result = diagnose_fit(
        spectrum,
        [ResonanceFit("short", "baseline", (), float("nan"), float("inf"), False, "failed")],
    )
    assert result.status == "FIT_FAILED"
    assert "optimization_failed" in result.warnings
