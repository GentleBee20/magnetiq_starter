"""Unit tests for research-only sinusoidal nuisance fitting."""
import numpy as np
import pytest

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.nuisance import fit_sinusoidal_nuisance, sinusoidal_model
from magnetiq.processing.resonance import evaluate_model, fit_spectrum


def test_sinusoidal_nuisance_recovers_centers_on_synthetic_interference() -> None:
    x = np.linspace(2.85, 2.89, 201)
    p = np.array([1.0, 0.0, 0.04, 2.865, 0.001, 0.035, 2.876, 0.0012])
    y = evaluate_model(x, p, 2)
    y += 0.009 * np.sin(2 * np.pi * (x - x[0]) / 0.006 + 0.7)
    spectrum = OdmrSpectrum("nuisance_test", tuple(x), tuple(y))
    baseline = fit_spectrum(spectrum, 2)
    result = fit_sinusoidal_nuisance(spectrum, baseline, periods_ghz=(0.006,))
    assert result.success
    assert result.period_ghz == 0.006
    assert len(result.parameters) == 10
    assert abs(result.parameters[3] - 2.865) < 0.0005
    assert abs(result.parameters[6] - 2.876) < 0.0005
    assert result.rmse < baseline.rmse
    assert np.allclose(sinusoidal_model(x, np.asarray(result.parameters), 0.006), y, atol=1e-5)


def test_invalid_period_rejected() -> None:
    x = np.linspace(2.85, 2.89, 101)
    y = np.ones_like(x)
    spectrum = OdmrSpectrum("invalid_period", tuple(x), tuple(y))
    baseline = fit_spectrum(spectrum, 2)
    with pytest.raises(ValueError):
        fit_sinusoidal_nuisance(spectrum, baseline, periods_ghz=(0.0,))
