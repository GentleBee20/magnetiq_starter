"""Tests for immutable run directories, provenance fingerprints and comparisons."""

from pathlib import Path

import pytest

from magnetiq.tracking import file_sha256, new_run_location, summarize_rows


def test_new_runs_never_reuse_directory(tmp_path: Path) -> None:
    first = new_run_location(tmp_path, "baseline")
    second = new_run_location(tmp_path, "updated")
    assert first.output_dir != second.output_dir
    assert first.output_dir.exists()
    assert second.output_dir.exists()
    assert first.tracking_uri.startswith("sqlite:///")


def test_fingerprint_is_content_based(tmp_path: Path) -> None:
    file = tmp_path / "input.zip"
    file.write_bytes(b"experiment A")
    original = file_sha256(file)
    file.write_bytes(b"experiment B")
    assert original != file_sha256(file)


def test_metrics_summarization() -> None:
    metrics = summarize_rows(
        [
            {"status": "FIT_OK", "rmse": 0.01, "normalized_rmse": 0.1, "max_local_rmse_ratio": 1.3},
            {
                "status": "REVIEW_REQUIRED",
                "rmse": 0.03,
                "normalized_rmse": 0.3,
                "max_local_rmse_ratio": None,
            },
        ]
    )
    assert metrics["spectra"] == 2
    assert metrics["fit_ok"] == 1
    assert metrics["median_rmse"] == pytest.approx(0.02)
