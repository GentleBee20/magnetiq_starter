"""Research-only period refinement regression checks."""

import numpy as np
import pytest

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.nuisance import NuisanceFit
from magnetiq.processing.period_refinement import conservative_selection, refine_period
from magnetiq.processing.resonance import evaluate_model, fit_spectrum


def test_refined_period_recovers_off_grid_oscillation() -> None:
    x = np.linspace(2.85, 2.89, 301)
    params = np.array([1.0, 0.0, 0.04, 2.865, 0.0011, 0.035, 2.876, 0.0012])
    y = evaluate_model(x, params, 2) + 0.01 * np.sin(2 * np.pi * (x - x[0]) / 0.0086 + 0.7)
    spectrum = OdmrSpectrum("off_grid", tuple(x), tuple(y))
    baseline = fit_spectrum(spectrum, 2)
    fit = refine_period(spectrum, baseline)
    assert fit.success
    assert fit.period_ghz is not None
    assert abs(fit.period_ghz - 0.0086) < 0.0002
    assert abs(fit.parameters[3] - 2.865) < 0.0005


def test_conservative_selection_requires_extra_evidence() -> None:
    baseline = fit_spectrum(
        OdmrSpectrum("test", tuple(np.linspace(2.85, 2.89, 101)), tuple(np.ones(101))), 2
    )
    nuisance = NuisanceFit(True, (), 0.006, 0.001, 0.001, baseline.aicc - 4, "test")
    assert conservative_selection(baseline, nuisance, extra_penalty=8).selected == "baseline"
    assert conservative_selection(baseline, nuisance, extra_penalty=2).selected == "nuisance"
    with pytest.raises(ValueError):
        conservative_selection(baseline, nuisance, extra_penalty=-1)
