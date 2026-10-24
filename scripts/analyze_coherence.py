"""Generate exploratory Ramsey/spin-echo fit-quality reports from original archive."""

from __future__ import annotations

import argparse
import csv
import html
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from magnetiq.coherence import analyze, iter_coherence


def run(archive: Path, output_dir: Path) -> int:
    """Write descriptive CSV, PNGs and an index HTML without changing input."""
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "plots"
    images_dir.mkdir(exist_ok=True)
    results = []
    for i, (source, values) in enumerate(iter_coherence(archive), 1):
        result = analyze(source, values)
        results.append(result)
        stem = re.sub(r"[^a-zA-Z0-9_-]", "_", Path(source).stem)[:65]
        plot_file = f"{i:03d}_{stem}.png"
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
        ax1.plot(values[:, 0], values[:, 1], ".", markersize=3, label="Data")
        ax1.plot(values[:, 0], values[:, 2], "-", linewidth=1.5, label="Author Fit")
        ax1.plot(values[:, 0], values[:, 3], "--", linewidth=1, label="Author Envelope")
        ax1.set_ylabel("Reported signal (units unspecified)")
        ax1.legend()
        ax2.axhline(0, linewidth=0.8, color="black")
        ax2.plot(values[:, 0], values[:, 1] - values[:, 2], linewidth=1)
        ax2.set_xlabel("tau [ns]")
        ax2.set_ylabel("Data minus Fit")
        fig.suptitle(f"{result.experiment}: {result.region} — descriptive fit diagnostics")
        fig.tight_layout()
        fig.savefig(images_dir / plot_file, dpi=140)
        plt.close(fig)
    if not results:
        raise ValueError("No valid spin-coherence text files found in archive")
    with (output_dir / "coherence_diagnostics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        rows = [result.as_row() for result in results]
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    items = []
    for i, result in enumerate(results, 1):
        stem = re.sub(r"[^a-zA-Z0-9_-]", "_", Path(result.source).stem)[:65]
        plot = f"plots/{i:03d}_{stem}.png"
        warnings = ", ".join(result.warnings) or "none"
        items.append(
            f"<tr><td>{html.escape(result.source)}</td>"
            f"<td>{result.normalized_rmse:.4g}</td>"
            f"<td>{html.escape(warnings)}</td>"
            f'<td><a href="{html.escape(plot)}">Plot</a></td></tr>'
        )
    report = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<title>MagnetIQ coherence fit diagnostics</title>"
        "<style>body{font:16px system-ui;max-width:1100px;margin:3rem auto;padding:1rem}"
        "table{border-collapse:collapse;width:100%;font-size:0.85rem}"
        "th,td{border-bottom:1px solid #ccc;padding:0.55rem;text-align:left}"
        "td:first-child{overflow-wrap:anywhere}</style></head><body>"
        "<h1>Coherence fit diagnostics</h1>"
        "<p><strong>Exploratory checks only.</strong> Author-provided Fit and Envelope"
        " are not ground truth. Relative errors use each measurement's Data range;"
        " do not compare raw RMSE across different signal scales. Warnings are"
        " uncalibrated and do not identify sensor defects.</p>"
        "<table><thead><tr><th>Measurement</th><th>Normalized RMSE</th>"
        "<th>Flags</th><th>Figure</th></tr></thead><tbody>"
        + "".join(items)
        + "</tbody></table></body></html>"
    )
    (output_dir / "coherence_report.html").write_text(report, encoding="utf-8")
    return len(results)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/coherence"))
    args = parser.parse_args()
    print(f"Analyzed {run(args.archive, args.output_dir)} coherence measurements")
    print(f"Report: {args.output_dir / 'coherence_report.html'}")


if __name__ == "__main__":
    main()
