"""Exploratory center stability; bootstrap is not calibrated uncertainty."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, cast

import numpy as np
from scipy import optimize

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.resonance import ResonanceFit, evaluate_model, fit_spectrum


class _Result(Protocol):
    x: np.ndarray
    success: bool


@dataclass(frozen=True)
class CenterStability:
    """Variability of fitted centers, in MHz; not a guarantee of accuracy."""

    bootstrap_successes: int
    bootstrap_trials: int
    bootstrap_width95_max_mhz: float | None
    multistart_successes: int
    multistart_trials: int
    multistart_range_max_mhz: float | None


def center_stability(
    spectrum: OdmrSpectrum,
    fit: ResonanceFit,
    *,
    seed: int = 42,
    bootstrap_trials: int = 30,
    multistart_trials: int = 12,
) -> CenterStability:
    """Refit fixed double-Lorentzian model using IID residual resampling and jittered starts.

    Does not reselect model order. IID resampling ignores correlation and can be
    misleading when the model is misspecified; assess empirical coverage separately.
    """
    if bootstrap_trials < 1 or multistart_trials < 1:
        raise ValueError("Trial counts must be positive")
    if fit.model != "double" or not fit.success or len(fit.parameters) != 8:
        return CenterStability(0, bootstrap_trials, None, 0, multistart_trials, None)

    frequency = np.asarray(spectrum.frequency_ghz, dtype=float)
    measured = np.asarray(spectrum.normalized_contrast, dtype=float)
    params = np.asarray(fit.parameters, dtype=float)
    prediction = evaluate_model(frequency, params, 2)
    residual = measured - prediction
    rng = np.random.default_rng(seed)
    bootstrap_centers: list[list[float]] = []
    for _ in range(bootstrap_trials):
        sampled = prediction + rng.choice(residual, size=len(residual), replace=True)
        synthetic = OdmrSpectrum(spectrum.source, tuple(frequency), tuple(sampled))
        refit = fit_spectrum(synthetic, 2)
        if refit.success and len(refit.parameters) == 8:
            bootstrap_centers.append(
                sorted([float(refit.parameters[3]), float(refit.parameters[6])])
            )

    span = float(np.ptp(frequency))
    spacing = float(np.median(np.diff(frequency)))
    signal_range = max(float(np.ptp(measured)), 1e-6)
    lower = np.asarray([
        float(np.min(measured)) - signal_range, -10 * signal_range / span,
        0, frequency[0], max(spacing / 4, 1e-9),
        0, frequency[0], max(spacing / 4, 1e-9),
    ])
    upper = np.asarray([
        float(np.max(measured)) + signal_range, 10 * signal_range / span,
        max(2 * signal_range, 1e-5), frequency[-1], span / 2,
        max(2 * signal_range, 1e-5), frequency[-1], span / 2,
    ])
    multistart_centers: list[list[float]] = []
    least_squares = cast(Callable[..., _Result], optimize.least_squares)
    for _ in range(multistart_trials):
        initial = params.copy()
        initial[3] += rng.normal(0, 0.0015)
        initial[6] += rng.normal(0, 0.0015)
        initial[2] *= rng.uniform(0.65, 1.35)
        initial[5] *= rng.uniform(0.65, 1.35)
        initial[4] *= rng.uniform(0.7, 1.3)
        initial[7] *= rng.uniform(0.7, 1.3)
        initial = np.clip(initial, lower + 1e-12, upper - 1e-12)
        result = least_squares(
            lambda p: evaluate_model(frequency, p, 2) - measured,
            x0=initial,
            bounds=(lower, upper),
            max_nfev=2000,
        )
        if result.success:
            multistart_centers.append(sorted([float(result.x[3]), float(result.x[6])]))

    width: float | None = None
    if len(bootstrap_centers) >= 2:
        array = np.asarray(bootstrap_centers)
        width = float(
            np.max(np.percentile(array, 97.5, axis=0) - np.percentile(array, 2.5, axis=0))
            * 1000
        )
    spread: float | None = None
    if len(multistart_centers) >= 2:
        array = np.asarray(multistart_centers)
        spread = float(np.max(np.ptp(array, axis=0)) * 1000)
    return CenterStability(
        len(bootstrap_centers),
        bootstrap_trials,
        width,
        len(multistart_centers),
        multistart_trials,
        spread,
    )
