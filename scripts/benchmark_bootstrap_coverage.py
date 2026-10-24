"""Measure empirical center-interval coverage on truth-known synthetic spectra.

Run: python -m scripts.benchmark_bootstrap_coverage
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import mlflow
import numpy as np

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.diagnostics import choose_fit
from magnetiq.processing.resonance import fit_spectrum
from magnetiq.processing.stability import center_stability
from magnetiq.tracking import EXPERIMENT, git_revision, new_run_location
from scripts.benchmark_ground_truth import make_cases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261224)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--bootstrap", type=int, default=20)
    parser.add_argument("--starts", type=int, default=3)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/odmr/experiments"))
    args = parser.parse_args()
    if min(args.repeats, args.bootstrap, args.starts) < 1:
        parser.error("All trial counts must be positive")

    cases = [
        case
        for case in make_cases(args.seed, args.repeats)
        if case[0].endswith(("clean_0", "oscillation_1", "oscillation_2"))
    ]
    rows: list[dict[str, object]] = []
    for index, (name, c1, c2, frequency, contrast) in enumerate(cases):
        spectrum = OdmrSpectrum(name, tuple(frequency), tuple(contrast))
        chosen = choose_fit([fit_spectrum(spectrum, n) for n in (0, 1, 2)])
        stability = center_stability(
            spectrum,
            chosen,
            seed=args.seed + index,
            bootstrap_trials=args.bootstrap,
            multistart_trials=args.starts,
        )
        truth = sorted((c1, c2))
        one = stability.bootstrap_interval_1_ghz
        two = stability.bootstrap_interval_2_ghz
        assessable = one is not None and two is not None
        joint_covered = bool(
            assessable
            and one is not None
            and two is not None
            and one[0] <= truth[0] <= one[1]
            and two[0] <= truth[1] <= two[1]
        )
        rows.append(
            {
                "case": name,
                "model": chosen.model,
                "assessable": assessable,
                "joint_covered": joint_covered if assessable else None,
                "bootstrap_successes": stability.bootstrap_successes,
                "bootstrap_trials": args.bootstrap,
                "max_interval_width_mhz": stability.bootstrap_width95_max_mhz,
            }
        )
    location = new_run_location(args.output_dir, "bootstrap-coverage-research")
    path = location.output_dir / "bootstrap_coverage.csv"
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    evaluable = [row for row in rows if row["assessable"]]
    coverage = (
        sum(bool(row["joint_covered"]) for row in evaluable) / len(evaluable)
        if evaluable
        else float("nan")
    )
    mlflow.set_tracking_uri(location.tracking_uri)
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=location.run_name) as active:
        mlflow.set_tags(
            {
                "project": "MagnetIQ",
                "pipeline": "synthetic-bootstrap-coverage",
                "git_revision": git_revision(),
                "quality_labels": "research-only",
            }
        )
        mlflow.log_params({"seed": args.seed, "repeats": args.repeats, "bootstrap": args.bootstrap})
        mlflow.log_metric("total_cases", float(len(rows)))
        mlflow.log_metric("assessable_cases", float(len(evaluable)))
        if np.isfinite(coverage):
            mlflow.log_metric("empirical_joint_coverage", coverage)
        mlflow.log_artifact(str(path), artifact_path="coverage")
        print(f"MLflow run: {active.info.run_id}")
    print(f"Assessable cases: {len(evaluable)}/{len(rows)}")
    print(f"Empirical joint coverage: {coverage:.3f}")
    print(f"Saved: {path}")
    print("Warning: correlated residuals violate IID-bootstrap assumptions.")


if __name__ == "__main__":
    main()
