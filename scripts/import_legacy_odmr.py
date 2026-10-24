"""Register a preserved pre-MLflow ODMR result folder as a historical run."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import mlflow

from magnetiq.tracking import EXPERIMENT, file_sha256, summarize_rows


def main() -> None:
    """Import without altering or moving preserved CSV and figures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="Preserved diagnostics folder")
    parser.add_argument("--run-name", default="baseline-before-local-residual-checks")
    parser.add_argument("--tracking-uri", default="sqlite:///reports/odmr/experiments/mlflow.db")
    parser.add_argument("--archive", type=Path, help="Raw archive used by the historical run")
    args = parser.parse_args()
    csv_path = args.snapshot / "fit_diagnostics.csv"
    if not csv_path.is_file():
        parser.error(f"Missing legacy diagnostics CSV: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        parser.error("Legacy CSV has no diagnostic rows")
    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=args.run_name) as active:
        mlflow.set_tags(
            {
                "project": "MagnetIQ",
                "pipeline": "odmr-fit-diagnostics",
                "provenance": "legacy-import; original run not replayed",
                "quality_labels": "provisional-fit-only",
                "dataset_sha256": (
                    file_sha256(args.archive) if args.archive is not None else "unknown"
                ),
                "source_revision": "unverified-historical",
            }
        )
        mlflow.log_param("imported_from", str(args.snapshot))
        mlflow.log_metrics(summarize_rows(rows))
        mlflow.log_artifacts(str(args.snapshot), artifact_path="reports")
        print(f"Imported historical run: {active.info.run_id}")


if __name__ == "__main__":
    main()
