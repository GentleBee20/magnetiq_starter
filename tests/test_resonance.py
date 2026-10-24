"""Controlled tests for physically interpretable resonance fitting."""

import numpy as np
import pytest

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.resonance import evaluate_model, fit_spectrum, lorentzian


def test_lorentzian_half_width():
    values = lorentzian(np.array([1.9, 2.0, 2.1]), 2.0, 0.1)
    assert values == pytest.approx([0.5, 1.0, 0.5])


def test_recovery_of_two_resonances():
    x = np.linspace(2.85, 2.89, 401)
    true = np.array([1.0, 0.0, 0.04, 2.866, 0.0012, 0.03, 2.875, 0.0015])
    y = evaluate_model(x, true, 2)
    spectrum = OdmrSpectrum("synthetic", tuple(x), tuple(y))
    baseline, single, double = [fit_spectrum(spectrum, n) for n in (0, 1, 2)]
    assert all(f.success for f in (baseline, single, double))
    assert double.rmse < single.rmse
    assert double.aicc < single.aicc
    assert sorted([double.parameters[3], double.parameters[6]]) == pytest.approx(
        [2.866, 2.875], abs=0.001
    )


def test_rejects_unsupported_model():
    spectrum = OdmrSpectrum("example", (2.85, 2.86), (1.0, 0.9))
    with pytest.raises(ValueError, match="n_peaks"):
        fit_spectrum(spectrum, 3)


def test_small_sample_returns_failure():
    spectrum = OdmrSpectrum("example", (2.85, 2.86), (1.0, 0.9))
    result = fit_spectrum(spectrum, 2)
    assert not result.success
