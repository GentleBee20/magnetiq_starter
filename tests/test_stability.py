"""Parameter stability smoke tests with explicitly controlled random seed."""

import numpy as np
import pytest

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.resonance import evaluate_model, fit_spectrum
from magnetiq.processing.stability import center_stability


def test_stability_on_clean_double_lorentzian() -> None:
    frequency = np.linspace(2.85, 2.89, 201)
    parameters = np.array([1.0, 0.0, 0.04, 2.865, 0.0011, 0.03, 2.876, 0.0013])
    rng = np.random.default_rng(44)
    observed = evaluate_model(frequency, parameters, 2) + rng.normal(0, 0.0005, len(frequency))
    spectrum = OdmrSpectrum("stability_test", tuple(frequency), tuple(observed))
    fit = fit_spectrum(spectrum, 2)
    result = center_stability(spectrum, fit, seed=18, bootstrap_trials=3, multistart_trials=3)
    assert result.bootstrap_successes >= 2
    assert result.multistart_successes >= 2
    assert result.bootstrap_width95_max_mhz is not None
    assert result.multistart_range_max_mhz is not None
    assert result.bootstrap_width95_max_mhz >= 0


def test_invalid_trial_counts_rejected() -> None:
    spectrum = OdmrSpectrum("dummy", (2.85, 2.86), (1.0, 0.9))
    fit = fit_spectrum(spectrum, 2)
    with pytest.raises(ValueError):
        center_stability(spectrum, fit, bootstrap_trials=0)


def test_near_optimal_restart_details() -> None:
    frequency = np.linspace(2.85, 2.89, 201)
    params = np.array([1.0, 0.0, 0.04, 2.865, 0.0011, 0.03, 2.876, 0.0013])
    signal = evaluate_model(frequency, params, 2)
    spectrum = OdmrSpectrum("near_optimal", tuple(frequency), tuple(signal))
    fit = fit_spectrum(spectrum, 2)
    result = center_stability(spectrum, fit, bootstrap_trials=3, multistart_trials=3, seed=24)
    assert result.near_optimal_count <= result.multistart_successes
    assert len(result.restart_details) == result.multistart_successes
    assert all(detail[2] >= 0 and detail[3] >= 0 for detail in result.restart_details)


def test_parametric_noise_requires_positive_std() -> None:
    frequency = np.linspace(2.85, 2.89, 101)
    params = np.array([1.0, 0.0, 0.04, 2.865, 0.0011, 0.03, 2.876, 0.0013])
    spectrum = OdmrSpectrum(
        "gaussian_test", tuple(frequency), tuple(evaluate_model(frequency, params, 2))
    )
    fit = fit_spectrum(spectrum, 2)
    with pytest.raises(ValueError):
        center_stability(spectrum, fit, gaussian_noise_std=0.0)
    result = center_stability(
        spectrum,
        fit,
        bootstrap_trials=3,
        multistart_trials=1,
        gaussian_noise_std=0.0006,
        seed=77,
    )
    assert result.bootstrap_successes == 3
    assert result.bootstrap_interval_1_ghz is not None
