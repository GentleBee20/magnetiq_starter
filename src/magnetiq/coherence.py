"""Read-only coherence signal diagnostics for Ramsey and spin-echo measurements.

The author-provided Fit is a comparison curve, not validated ground truth.
"""

from __future__ import annotations

import csv
import io
import math
import zipfile
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class CoherenceResult:
    source: str
    experiment: str
    region: str
    n_points: int
    tau_min_ns: float
    tau_max_ns: float
    rmse: float
    normalized_rmse: float
    lag1_residual_correlation: float | None
    max_local_rmse_ratio: float
    scale: float
    mean_residual: float
    signed_bias_over_rmse: float
    early_late_bias_difference_over_rmse: float
    sampling_step_max_min_ratio: float
    warnings: tuple[str, ...]

    def as_row(self) -> dict[str, str | int | float | None]:
        result = asdict(self)
        result["warnings"] = ";".join(self.warnings)
        return result


def read_measurement(data: bytes) -> np.ndarray:
    """Validate four-column numeric time series with strictly increasing time."""
    text = data.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if header is None or [v.strip() for v in header] != ["tau [ns]", "Data", "Fit", "Envelope"]:
        raise ValueError("expected columns tau [ns],Data,Fit,Envelope")
    try:
        values = np.array(
            [[float(value) for value in row] for row in reader if row],
            dtype=float,
        )
    except (ValueError, TypeError) as exc:
        raise ValueError("non-numeric measurement values") from exc
    if values.ndim != 2 or values.shape[1] != 4 or len(values) < 5:
        raise ValueError("at least five four-column samples required")
    if not np.all(np.isfinite(values)):
        raise ValueError("nonfinite measurement values")
    if not np.all(np.diff(values[:, 0]) > 0):
        raise ValueError("tau must be strictly increasing")
    return values


def analyze(source: str, values: np.ndarray) -> CoherenceResult:
    """Compute descriptive residual statistics without asserting physical accuracy."""
    data = values[:, 1]
    fit = values[:, 2]
    residual = data - fit
    rmse = float(np.sqrt(np.mean(residual**2)))
    # Data range is invariant under additive offset, but it can be near zero.
    scale = float(np.ptp(data))
    if scale <= max(1e-12, 1e-12 * float(np.max(np.abs(data)))):
        scale = float("nan")
    nrmse = rmse / scale if math.isfinite(scale) else float("nan")
    if float(np.std(residual[:-1])) > 0 and float(np.std(residual[1:])) > 0:
        lag1 = float(np.corrcoef(residual[:-1], residual[1:])[0, 1])
    else:
        lag1 = None
    # Purely descriptive diagnostics: no new pass/fail thresholds.
    mean_residual = float(np.mean(residual))
    signed_bias_over_rmse = mean_residual / rmse if rmse > 0 else 0.0
    midpoint = len(residual) // 2
    early_late_difference = float(
        np.mean(residual[midpoint:]) - np.mean(residual[:midpoint])
    )
    early_late_bias_difference_over_rmse = (
        early_late_difference / rmse if rmse > 0 else 0.0
    )
    steps = np.diff(values[:, 0])
    sampling_step_max_min_ratio = float(np.max(steps) / np.min(steps))
    global_rms = max(rmse, 1e-15)
    chunks = np.array_split(residual, min(5, len(residual)))
    local_ratio = float(max(np.sqrt(np.mean(chunk**2)) / global_rms for chunk in chunks))
    name = Path(source).name.lower()
    experiment = "ramsey" if "ramsey" in name else "spin_echo" if "spinecho" in name else "unknown"
    region = (
        "no_hole"
        if "no hole region" in source.lower()
        else "hole"
        if "hole region" in source.lower()
        else "unknown"
    )
    warnings = []
    if not math.isfinite(nrmse):
        warnings.append("undefined_signal_scale")
    if lag1 is not None and abs(lag1) > 0.6:
        warnings.append("structured_residuals_exploratory")
    if local_ratio > 1.8:
        warnings.append("localized_residual_excess_exploratory")
    return CoherenceResult(
        source=source,
        experiment=experiment,
        region=region,
        n_points=len(values),
        tau_min_ns=float(values[0, 0]),
        tau_max_ns=float(values[-1, 0]),
        rmse=rmse,
        normalized_rmse=nrmse,
        lag1_residual_correlation=lag1,
        max_local_rmse_ratio=local_ratio,
        scale=scale,
        mean_residual=mean_residual,
        signed_bias_over_rmse=signed_bias_over_rmse,
        early_late_bias_difference_over_rmse=early_late_bias_difference_over_rmse,
        sampling_step_max_min_ratio=sampling_step_max_min_ratio,
        warnings=tuple(warnings),
    )


def iter_coherence(archive: Path) -> Iterator[tuple[str, np.ndarray]]:
    """Yield validated coherence measurements directly from original archive."""
    with zipfile.ZipFile(archive) as zf:
        for name in sorted(zf.namelist()):
            if "spin coherence/" not in name.lower() or not name.lower().endswith(".txt"):
                continue
            yield name, read_measurement(zf.read(name))
