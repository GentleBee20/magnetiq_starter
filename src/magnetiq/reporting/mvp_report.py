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
    rows: list[str] = []
    for index, result in enumerate(results, start=1):
        filename = f"{index:03d}_{Path(result.source).stem}.png"
        plot_path = output_dir / "plots" / filename
        plot_link = (
            '<a href="plots/' + escape(filename, quote=True) + '">View fit plot</a>'
            if plot_path.is_file()
            else '<span class="muted">Plot unavailable</span>'
        )
        explanations = describe_warnings(result.warnings)
        warnings = (
            "<ul>"
            + "".join(
                "<li><strong>"
                + escape(item["code"])
                + "</strong> · "
                + escape(item["investigation_stage"])
                + "<div>"
                + escape(item["interpretation"])
                + " "
                + escape(item["next_check"])
                + "</div></li>"
                for item in explanations
            )
            + "</ul>"
            if explanations
            else '<span class="muted">No provisional warnings</span>'
        )
        status_class = "ok" if result.status == "FIT_OK" else "review"
        rows.append(
            "<tr><td>"
            + str(index)
            + "</td><td class='source'>"
            + escape(result.source)
            + "</td><td><span class='status "
            + status_class
            + "'>"
            + escape(result.status)
            + "</span></td><td>"
            + escape(result.model)
            + "</td><td>"
            + warnings
            + "</td><td>"
            + plot_link
            + "</td></tr>"
        )
    total = len(results)
    report_css = """
    :root{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#18263b;
    background:#f5f7fb}*{box-sizing:border-box}body{margin:0}
    main{max-width:1440px;margin:auto;padding:36px 24px 70px}
    h1{margin:0 0 8px;font-size:2rem}p{line-height:1.6}
    .scope{color:#52627b;max-width:850px}.cards{display:flex;flex-wrap:wrap;
    gap:14px;margin:26px 0}.card{background:white;border:1px solid #dce3ec;
    border-radius:12px;padding:18px 24px;min-width:170px}
    .card strong{display:block;font-size:2rem}.card span{color:#52627b}
    .links{display:flex;gap:20px;flex-wrap:wrap;margin:22px 0}
    a{color:#1855a5}.table-wrap{overflow-x:auto;background:white;
    border:1px solid #dce3ec;border-radius:12px}table{border-collapse:collapse;
    width:100%;font-size:.89rem}th,td{padding:14px 12px;text-align:left;
    border-bottom:1px solid #e6ebf2;vertical-align:top}th{background:#eaf0f7;
    white-space:nowrap}tr:hover{background:#f7faff}.source{min-width:230px;
    overflow-wrap:anywhere;max-width:420px}.status{display:inline-block;
    border-radius:999px;padding:4px 9px;font-weight:700;font-size:.77rem}
    .ok{background:#e3f4ea;color:#17633e}.review{background:#fff0cf;
    color:#805200}.muted{color:#69768a}td ul{margin:0;padding-left:18px;
    min-width:250px}td li+li{margin-top:12px}td li div{margin-top:3px}
    .note{border-left:3px solid #7994b8;padding-left:12px}
    @media(max-width:700px){main{padding:20px 12px}h1{font-size:1.6rem}}
    """
    html = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>MagnetIQ · ODMR measurement quality</title><style>"
        + report_css
        + "</style></head><body><main><header>"
        "<h1>MagnetIQ · ODMR fit quality</h1>"
        "<p class='scope'>Provisional spectral fit verdicts only: "
        "not sensor calibration, field-map confidence or physical fault diagnoses.</p>"
        "</header><section class='cards' aria-label='Analysis summary'>"
        "<div class='card'><strong>"
        + str(total)
        + "</strong><span>Measurements</span></div>"
        "<div class='card'><strong>"
        + str(counts.get("FIT_OK", 0))
        + "</strong><span>FIT_OK</span></div>"
        "<div class='card'><strong>"
        + str(counts.get("REVIEW_REQUIRED", 0))
        + "</strong><span>REVIEW_REQUIRED</span></div>"
        "<div class='card'><strong>"
        + str(counts.get("FIT_FAILED", 0))
        + "</strong><span>FIT_FAILED</span></div></section>"
        "<nav class='links' aria-label='Supporting evidence'>"
        "<a href='measurement_report.json'>Machine-readable JSON</a>"
        "<a href='fit_diagnostics.csv'>Diagnostics CSV</a>"
        "<a href='summary.png'>Summary plot</a>"
        "<a href='manifest.json'>Run manifest</a></nav>"
        "<p class='note'>A review flag means a heuristic fit-quality check "
        "requires investigation; it is not a confirmed physical defect.</p>"
        "<h2>Per-spectrum results</h2><div class='table-wrap'>"
        "<table><thead><tr><th>#</th><th>Source</th><th>Fit status</th>"
        "<th>Model</th><th>Evidence and suggested investigation</th>"
        "<th>Plot</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div></main></body></html>"
    )
    (output_dir / "measurement_report.html").write_text(html, encoding="utf-8")
