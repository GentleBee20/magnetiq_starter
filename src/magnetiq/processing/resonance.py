"""Constrained Lorentzian fitting for ODMR spectra; no quality verdicts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, cast

import numpy as np
from scipy import optimize
from scipy.signal import find_peaks

from magnetiq.data.odmr import OdmrSpectrum


class _LeastSquaresResult(Protocol):
    """Fields consumed from SciPy's optimization result."""

    x: np.ndarray
    success: bool
    message: str


@dataclass(frozen=True)
class ResonanceFit:
    """Model-fitting diagnostics; centers and linewidths are in GHz."""

    source: str
    model: str
    parameters: tuple[float, ...]
    rmse: float
    aicc: float
    success: bool
    reason: str


def lorentzian(frequency: np.ndarray, center: float, width: float) -> np.ndarray:
    """Unit-amplitude Lorentzian with half-width at half-maximum 'width'."""
    return width**2 / ((frequency - center) ** 2 + width**2)


def evaluate_model(frequency: np.ndarray, parameters: np.ndarray, n_peaks: int) -> np.ndarray:
    """Evaluate a linear baseline plus n negative Lorentzian dips."""
    relative = frequency - float(np.mean(frequency))
    prediction = parameters[0] + parameters[1] * relative
    for index in range(n_peaks):
        offset = 2 + 3 * index
        amplitude, center, width = parameters[offset : offset + 3]
        prediction = prediction - amplitude * lorentzian(frequency, center, width)
    return np.asarray(prediction, dtype=float)


def fit_spectrum(spectrum: OdmrSpectrum, n_peaks: int) -> ResonanceFit:
    """Fit 0, 1 or 2 dips with bounded nonlinear least squares.

    AICc is an exploratory model comparison criterion, not a measurement
    reliability verdict. Fits that fail remain explicit failures.
    """
    if n_peaks not in (0, 1, 2):
        raise ValueError("n_peaks must be 0, 1 or 2")

    x = np.asarray(spectrum.frequency_ghz, dtype=float)
    y = np.asarray(spectrum.normalized_contrast, dtype=float)
    count = len(x)
    parameter_count = 2 + 3 * n_peaks
    name = ("baseline", "single", "double")[n_peaks]
    if count <= parameter_count + 1:
        return ResonanceFit(
            spectrum.source,
            name,
            (),
            float("nan"),
            float("inf"),
            False,
            "Insufficient observations for AICc",
        )

    span = float(np.ptp(x))
    spacing = float(np.median(np.diff(x)))
    signal_range = max(float(np.ptp(y)), 1e-6)
    baseline = float(np.percentile(y, 90))
    initial = [baseline, 0.0]
    lower = [float(np.min(y)) - signal_range, -10 * signal_range / span]
    upper = [float(np.max(y)) + signal_range, 10 * signal_range / span]

    # Coarse peak selection avoids relying on one noisy global minimum.
    if n_peaks:
        prominence = max(signal_range * 0.12, 1e-7)
        indices, _ = find_peaks(-y, prominence=prominence, distance=max(2, count // 15))
        candidates = sorted((int(index) for index in indices), key=lambda index: y[index])
        for index in np.argsort(y):
            if all(abs(int(index) - chosen) > max(2, count // 15) for chosen in candidates):
                candidates.append(int(index))
            if len(candidates) >= n_peaks:
                break
        selected = sorted(candidates[:n_peaks], key=lambda index: x[index])
        for index in selected:
            initial.extend(
                [max(baseline - y[index], 1e-6), float(x[index]), max(spacing * 3, span / 30)]
            )
            lower.extend([0.0, float(x[0]), max(spacing / 4, 1e-9)])
            upper.extend([max(2 * signal_range, 1e-5), float(x[-1]), span / 2])

    try:
        # scipy-stubs may resolve this SciPy public function as a module.
        least_squares = cast(Callable[..., _LeastSquaresResult], optimize.least_squares)
        fitted = least_squares(
            lambda p: evaluate_model(x, p, n_peaks) - y,
            x0=np.asarray(initial),
            bounds=(np.asarray(lower), np.asarray(upper)),
            max_nfev=5000,
        )
        residual = evaluate_model(x, fitted.x, n_peaks) - y
        rss = max(float(np.dot(residual, residual)), np.finfo(float).tiny)
        rmse = float(np.sqrt(rss / count))
        aic = count * np.log(rss / count) + 2 * parameter_count
        aicc = float(
            aic + 2 * parameter_count * (parameter_count + 1) / (count - parameter_count - 1)
        )
        return ResonanceFit(
            spectrum.source,
            name,
            tuple(float(v) for v in fitted.x),
            rmse,
            aicc,
            bool(fitted.success),
            fitted.message,
        )
    except (ValueError, FloatingPointError) as exc:
        return ResonanceFit(spectrum.source, name, (), float("nan"), float("inf"), False, str(exc))
