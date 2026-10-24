"""Experimental continuous period refinement and penalized model selection."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, cast

import numpy as np
from scipy import optimize

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.nuisance import NuisanceFit, fit_sinusoidal_nuisance, sinusoidal_model
from magnetiq.processing.resonance import ResonanceFit


class _Result(Protocol):
    x: np.ndarray
    success: bool


@dataclass(frozen=True)
class Selection:
    """A research decision with a configurable extra period-search penalty."""

    selected: str
    adjusted_delta_aicc: float


def conservative_selection(
    baseline: ResonanceFit, nuisance: NuisanceFit, *, extra_penalty: float = 8.0
) -> Selection:
    """Select nuisance only if AICc improvement exceeds an extra penalty.

    This is a deliberately conservative heuristic, not a calibrated
    multiple-testing correction. Evaluate its false-selection rate.
    """
    if extra_penalty < 0:
        raise ValueError("extra_penalty must be nonnegative")
    delta = baseline.aicc - nuisance.aicc - extra_penalty
    return Selection("nuisance" if nuisance.success and delta > 0 else "baseline", delta)


def refine_period(
    spectrum: OdmrSpectrum,
    baseline: ResonanceFit,
    *,
    periods_ghz: tuple[float, ...] = (0.004, 0.005, 0.006, 0.007, 0.008, 0.009),
) -> NuisanceFit:
    """Jointly refine 11 parameters from the best discrete-period solution.

    The period remains bounded by the candidate-grid extremes. This
    does not validate period identification or correct model selection.
    """
    fixed = fit_sinusoidal_nuisance(spectrum, baseline, periods_ghz=periods_ghz)
    if not fixed.success or fixed.period_ghz is None:
        return fixed
    x = np.asarray(spectrum.frequency_ghz, dtype=float)
    y = np.asarray(spectrum.normalized_contrast, dtype=float)
    span = float(np.ptp(x))
    spacing = float(np.median(np.diff(x)))
    signal_range = max(float(np.ptp(y)), 1e-6)
    lower = np.asarray(
        [
            float(np.min(y)) - signal_range,
            -10 * signal_range / span,
            0.0,
            float(x[0]),
            max(spacing / 4, 1e-9),
            0.0,
            float(x[0]),
            max(spacing / 4, 1e-9),
            -2 * signal_range,
            -2 * signal_range,
            min(periods_ghz),
        ]
    )
    upper = np.asarray(
        [
            float(np.max(y)) + signal_range,
            10 * signal_range / span,
            max(2 * signal_range, 1e-5),
            float(x[-1]),
            span / 2,
            max(2 * signal_range, 1e-5),
            float(x[-1]),
            span / 2,
            2 * signal_range,
            2 * signal_range,
            max(periods_ghz),
        ]
    )
    initial = np.asarray([*fixed.parameters, fixed.period_ghz], dtype=float)
    initial = np.clip(initial, lower + 1e-12, upper - 1e-12)
    least_squares = cast(Callable[..., _Result], optimize.least_squares)

    def residual(p: np.ndarray) -> np.ndarray:
        return cast(np.ndarray, sinusoidal_model(x, p[:10], float(p[10])) - y)

    result = least_squares(
        residual,
        x0=initial,
        bounds=(lower, upper),
        max_nfev=2400,
        x_scale="jac",
    )
    if not result.success or not np.all(np.isfinite(result.x)):
        return fixed
    residuals = residual(result.x)
    rss = max(float(np.dot(residuals, residuals)), np.finfo(float).tiny)
    n, k = len(x), 11
    aicc = float(n * np.log(rss / n) + 2 * k + 2 * k * (k + 1) / (n - k - 1))
    return NuisanceFit(
        True,
        tuple(float(v) for v in result.x[:10]),
        float(result.x[10]),
        float(np.hypot(result.x[8], result.x[9])),
        float(np.sqrt(rss / n)),
        aicc,
        "continuous period refinement",
    )
