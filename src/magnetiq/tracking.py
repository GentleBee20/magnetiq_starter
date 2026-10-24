"""Reproducible, locally stored experiment records for ODMR diagnostics."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import mlflow
import numpy as np
import scipy

EXPERIMENT = "magnetiq-odmr-fit-quality"


@dataclass(frozen=True)
class RunLocation:
    """Uniquely identified run output and MLflow tracking location."""

    output_dir: Path
    run_name: str
    tracking_uri: str


def file_sha256(path: Path) -> str:
    """Fingerprint input bytes without extracting or changing a dataset."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision() -> str:
    """Return the exact source revision, or an explicit unknown marker."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def new_run_location(
    root: Path, run_name: str | None = None, tracking_uri: str | None = None
) -> RunLocation:
    """Allocate a new output directory; never reuse an existing output directory."""
    created = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    identifier = uuid.uuid4().hex[:10]
    resolved_name = run_name or f"odmr-{created}-{identifier}"
    output_dir = root / "runs" / f"{created}_{identifier}"
    output_dir.mkdir(parents=True, exist_ok=False)
    default_uri = f"sqlite:///{(root / 'mlflow.db').as_posix()}"
    uri = tracking_uri or os.environ.get("MLFLOW_TRACKING_URI") or default_uri
    return RunLocation(output_dir, resolved_name, uri)


def summarize_rows(rows: list[dict[str, object]]) -> dict[str, float]:
    """Calculate logged batch totals without claiming scientific classification accuracy."""
    totals = {
        "spectra": float(len(rows)),
        "fit_ok": float(sum(row["status"] == "FIT_OK" for row in rows)),
        "review_required": float(sum(row["status"] == "REVIEW_REQUIRED" for row in rows)),
        "fit_failed": float(sum(row["status"] == "FIT_FAILED" for row in rows)),
    }
    for key in ("rmse", "normalized_rmse", "max_local_rmse_ratio"):
        values = [float(value) for row in rows if isinstance((value := row.get(key)), (int, float))]
        finite = [value for value in values if np.isfinite(value)]
        if finite:
            totals[f"median_{key}"] = float(np.median(finite))
    return totals


@contextmanager
def tracked_run(
    location: RunLocation, archive: Path, *, limit: int, spectrum_count: int
) -> Iterator[str]:
    """Log run provenance and artifacts; propagate execution failures to MLflow."""
    mlflow.set_tracking_uri(location.tracking_uri)
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=location.run_name) as active:
        mlflow.set_tags(
            {
                "project": "MagnetIQ",
                "git_revision": git_revision(),
                "dataset_sha256": file_sha256(archive),
                "dataset_filename": archive.name,
                "python_version": platform.python_version(),
                "numpy_version": np.__version__,
                "scipy_version": scipy.__version__,
                "pipeline": "odmr-fit-diagnostics",
                "quality_labels": "provisional-fit-only",
            }
        )
        mlflow.log_params(
            {
                "limit": limit,
                "spectra_loaded": spectrum_count,
                "candidate_models": "baseline,single,double",
                "fit_selection": "minimum-finite-AICc",
                "local_rmse_ratio_threshold": 2.0,
                "local_bias_ratio_threshold": 1.0,
                "relative_rmse_threshold": 0.15,
                "residual_lag1_threshold": 0.7,
                "aicc_ambiguity_threshold": 2.0,
            }
        )
        try:
            yield active.info.run_id
        finally:
            if location.output_dir.exists():
                mlflow.log_artifacts(str(location.output_dir), artifact_path="reports")


def write_manifest(output: Path, *, run_id: str, tracking_uri: str, archive_sha256: str) -> None:
    """Persist a small machine-readable run manifest alongside CSV and plots."""
    output.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "tracking_uri": tracking_uri,
                "dataset_sha256": archive_sha256,
                "git_revision": git_revision(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
