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
    near_optimal_range_max_mhz: float | None = None
    near_optimal_count: int = 0
    restart_details: tuple[tuple[float, float, float, float, bool], ...] = ()
    bootstrap_interval_1_ghz: tuple[float, float] | None = None
    bootstrap_interval_2_ghz: tuple[float, float] | None = None


def center_stability(
    spectrum: OdmrSpectrum,
    fit: ResonanceFit,
    *,
    seed: int = 42,
    bootstrap_trials: int = 30,
    multistart_trials: int = 12,
    near_optimal_rss_ratio: float = 1.01,
    center_residuals: bool = False,
    gaussian_noise_std: float | None = None,
) -> CenterStability:
    """Refit fixed double-Lorentzian model using IID residual resampling and jittered starts.

    Does not reselect model order. IID resampling ignores correlation and can be
    misleading when the model is misspecified; assess empirical coverage separately.
    """
    if gaussian_noise_std is not None and gaussian_noise_std <= 0:
        raise ValueError("gaussian_noise_std must be positive")
    if near_optimal_rss_ratio < 1.0:
        raise ValueError("near_optimal_rss_ratio must be >= 1")
    if bootstrap_trials < 1 or multistart_trials < 1:
        raise ValueError("Trial counts must be positive")
    if fit.model != "double" or not fit.success or len(fit.parameters) != 8:
        return CenterStability(0, bootstrap_trials, None, 0, multistart_trials, None)

    frequency = np.asarray(spectrum.frequency_ghz, dtype=float)
    measured = np.asarray(spectrum.normalized_contrast, dtype=float)
    params = np.asarray(fit.parameters, dtype=float)
    prediction = evaluate_model(frequency, params, 2)
    residual = measured - prediction
    if center_residuals:
        residual = residual - float(np.mean(residual))
    rng = np.random.default_rng(seed)
    bootstrap_centers: list[list[float]] = []
    for _ in range(bootstrap_trials):
        noise = (
            rng.normal(0.0, gaussian_noise_std, len(residual))
            if gaussian_noise_std is not None
            else rng.choice(residual, size=len(residual), replace=True)
        )
        sampled = prediction + noise
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
    restart_details: list[tuple[float, float, float, float, bool]] = []
    baseline_rss = float(np.sum(residual**2))
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
            centers = sorted([float(result.x[3]), float(result.x[6])])
            rss = float(np.sum((evaluate_model(frequency, result.x, 2) - measured) ** 2))
            boundary = bool(
                np.any((result.x - lower) <= 1e-5 * (upper - lower))
                or np.any((upper - result.x) <= 1e-5 * (upper - lower))
            )
            multistart_centers.append(centers)
            restart_details.append(
                (centers[0], centers[1], rss, rss / max(baseline_rss, 1e-30), boundary)
            )

    interval_1: tuple[float, float] | None = None
    interval_2: tuple[float, float] | None = None
    width: float | None = None
    if len(bootstrap_centers) >= 2:
        array = np.asarray(bootstrap_centers)
        bounds = np.percentile(array, [2.5, 97.5], axis=0)
        interval_1 = (float(bounds[0, 0]), float(bounds[1, 0]))
        interval_2 = (float(bounds[0, 1]), float(bounds[1, 1]))
        width = float(
            np.max(np.percentile(array, 97.5, axis=0) - np.percentile(array, 2.5, axis=0))
            * 1000
        )
    spread: float | None = None
    if len(multistart_centers) >= 2:
        array = np.asarray(multistart_centers)
        spread = float(np.max(np.ptp(array, axis=0)) * 1000)
    near = [
        [detail[0], detail[1]]
        for detail in restart_details
        if detail[3] <= near_optimal_rss_ratio
    ]
    near_range = (
        float(np.max(np.ptp(np.asarray(near), axis=0)) * 1000)
        if len(near) >= 2
        else None
    )
    return CenterStability(
        len(bootstrap_centers),
        bootstrap_trials,
        width,
        len(multistart_centers),
        multistart_trials,
        spread,
        near_range,
        len(near),
        tuple(restart_details),
        interval_1,
        interval_2,
    )
