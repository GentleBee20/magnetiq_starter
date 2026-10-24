"""Tests for the portable research-only measurement report."""

import json

from magnetiq.reporting.mvp_report import write_measurement_report


def test_empty_report_is_valid_and_explicit(tmp_path):
    write_measurement_report([], tmp_path)
    data = json.loads((tmp_path / "measurement_report.json").read_text(encoding="utf-8"))
    assert data["status_counts"] == {}
    assert data["measurements"] == []
    assert "not sensor calibration" in data["scope"]
    assert "Provisional spectral fit verdicts" in (
        tmp_path / "measurement_report.html"
    ).read_text(encoding="utf-8")
