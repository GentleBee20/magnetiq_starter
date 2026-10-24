"""Research-only double-Lorentzian plus sinusoidal nuisance fitting."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, cast

import numpy as np
from scipy import optimize

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.resonance import ResonanceFit, evaluate_model


class _FitResult(Protocol):
    x: np.ndarray
    success: bool


@dataclass(frozen=True)
class NuisanceFit:
    """Result of the best fit across prespecified periods."""

    success: bool
    parameters: tuple[float, ...]
    period_ghz: float | None
    amplitude: float | None
    rmse: float
    aicc: float
    reason: str


def sinusoidal_model(
    frequency: np.ndarray, parameters: np.ndarray, period_ghz: float
) -> np.ndarray:
    """Evaluate two dips plus a sinusoidal empirical disturbance."""
    phase = 2 * np.pi * (frequency - float(frequency[0])) / period_ghz
    return np.asarray(
        evaluate_model(frequency, parameters[:8], 2)
        + (parameters[8] * np.sin(phase) + parameters[9] * np.cos(phase)),
        dtype=float,
    )


def fit_sinusoidal_nuisance(
    spectrum: OdmrSpectrum,
    baseline_fit: ResonanceFit,
    *,
    periods_ghz: tuple[float, ...] = (0.004, 0.005, 0.006, 0.007, 0.008, 0.009),
) -> NuisanceFit:
    """Refit both centers and nuisance for each fixed trial period.

    The reported AICc does NOT correct for searching across trial periods.
    This model is research-only and does not alter operational QC.
    """
    if not periods_ghz or any(p <= 0 for p in periods_ghz):
        raise ValueError("All trial periods must be positive")
    if (
        baseline_fit.model != "double"
        or not baseline_fit.success
        or len(baseline_fit.parameters) != 8
    ):
        return NuisanceFit(False, (), None, None, float("nan"), float("inf"), "No valid double fit")
    x = np.asarray(spectrum.frequency_ghz, dtype=float)
    y = np.asarray(spectrum.normalized_contrast, dtype=float)
    n = len(x)
    if n <= 11:
        return NuisanceFit(False, (), None, None, float("nan"), float("inf"), "Too few samples")
    span = float(np.ptp(x))
    spacing = float(np.median(np.diff(x)))
    signal_range = max(float(np.ptp(y)), 1e-6)
    lower = np.asarray(
        [
            float(np.min(y)) - signal_range,
            -10 * signal_range / span,
            0,
            x[0],
            max(spacing / 4, 1e-9),
            0,
            x[0],
            max(spacing / 4, 1e-9),
            -2 * signal_range,
            -2 * signal_range,
        ]
    )
    upper = np.asarray(
        [
            float(np.max(y)) + signal_range,
            10 * signal_range / span,
            max(2 * signal_range, 1e-5),
            x[-1],
            span / 2,
            max(2 * signal_range, 1e-5),
            x[-1],
            span / 2,
            2 * signal_range,
            2 * signal_range,
        ]
    )
    initial = np.clip(
        np.r_[np.asarray(baseline_fit.parameters), 0.0, 0.0],
        lower + 1e-12,
        upper - 1e-12,
    )
    best: NuisanceFit | None = None
    least_squares = cast(Callable[..., _FitResult], optimize.least_squares)
    for period in periods_ghz:

        def residual_function(p: np.ndarray, *, trial_period: float = period) -> np.ndarray:
            return cast(np.ndarray, sinusoidal_model(x, p, trial_period) - y)

        fitted = least_squares(
            residual_function,
            x0=initial,
            bounds=(lower, upper),
            max_nfev=1600,
        )
        if not fitted.success or not np.all(np.isfinite(fitted.x)):
            continue
        residual = sinusoidal_model(x, fitted.x, period) - y
        rss = max(float(np.dot(residual, residual)), np.finfo(float).tiny)
        k = 10
        aicc = float(n * np.log(rss / n) + 2 * k + 2 * k * (k + 1) / (n - k - 1))
        candidate = NuisanceFit(
            True,
            tuple(float(v) for v in fitted.x),
            float(period),
            float(np.hypot(fitted.x[8], fitted.x[9])),
            float(np.sqrt(rss / n)),
            aicc,
            "converged",
        )
        if best is None or candidate.aicc < best.aicc:
            best = candidate
    if best is None:
        return NuisanceFit(False, (), None, None, float("nan"), float("inf"), "Optimizers failed")
    return best
