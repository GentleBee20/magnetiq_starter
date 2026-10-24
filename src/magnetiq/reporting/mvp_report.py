"""Portable research-only report for ODMR fit diagnostics."""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import asdict
from html import escape
from pathlib import Path
from typing import Any

from magnetiq.processing.diagnostics import FitDiagnostics
from magnetiq.reporting.artifact_catalogue import describe_warnings


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def write_measurement_report(results: list[FitDiagnostics], output_dir: Path) -> None:
    """Create transparent supplementary reports without altering decisions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    counts = dict(Counter(result.status for result in results))
    data = {
        "schema_version": "0.1.0",
        "scope": "Provisional ODMR fit diagnostics; not sensor calibration or field-map validation",
        "status_counts": counts,
        "measurements": [
            {**asdict(result), "artifact_explanations": describe_warnings(result.warnings)}
            for result in results
        ],
    }
    (output_dir / "measurement_report.json").write_text(
        json.dumps(_json_safe(data), indent=2, allow_nan=False), encoding="utf-8"
    )
    rows = "".join(
        "<tr><td>"
        + escape(result.source)
        + "</td><td>"
        + escape(result.status)
        + "</td><td>"
        + escape(result.model)
        + "</td><td>"
        + escape(
            "; ".join(
                explanation["code"]
                + " ("
                + explanation["investigation_stage"]
                + "): "
                + explanation["next_check"]
                for explanation in describe_warnings(result.warnings)
            )
            or "No provisional warnings"
        )
        + "</td></tr>"
        for result in results
    )
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>MagnetIQ measurement quality report</title></head><body>"
        "<h1>MagnetIQ ODMR fit quality</h1>"
        "<p>Provisional spectral fit verdicts only; not sensor calibration, "
        "field-map confidence, or physical fault diagnoses.</p>"
        "<p>Measurements: " + str(len(results)) + "</p>"
        "<p>Status counts: " + escape(str(counts)) + "</p>"
        "<p>Supporting evidence: fit_diagnostics.csv, summary.png, plots/</p>"
        "<table border='1'><tr><th>Source</th><th>Status</th>"
        "<th>Model</th><th>Reason codes</th></tr>" + rows + "</table>"
        "</body></html>"
    )
    (output_dir / "measurement_report.html").write_text(html, encoding="utf-8")
