"""Compare center stability on representative held-out synthetic spectra.

Run as module: python -m scripts.benchmark_stability
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
    parser.add_argument("--seed", type=int, default=20261124)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--bootstrap", type=int, default=20)
    parser.add_argument("--starts", type=int, default=8)
    parser.add_argument("--tolerance-mhz", type=float, default=0.5)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/odmr/experiments"))
    args = parser.parse_args()
    if min(args.repeats, args.bootstrap, args.starts) < 1 or args.tolerance_mhz <= 0:
        parser.error("Positive repeats, bootstrap, starts and tolerance required")
    selected = [
        case for case in make_cases(args.seed, args.repeats)
        if case[0].endswith(("clean_0", "oscillation_1", "oscillation_2"))
    ]
    location = new_run_location(args.output_dir, "center-stability-research")
    rows: list[dict[str, object]] = []
    for index, (name, c1, c2, frequency, contrast) in enumerate(selected):
        spectrum = OdmrSpectrum(name, tuple(frequency), tuple(contrast))
        best = choose_fit([fit_spectrum(spectrum, n) for n in (0, 1, 2)])
        stability = center_stability(
            spectrum, best, seed=args.seed + index,
            bootstrap_trials=args.bootstrap, multistart_trials=args.starts,
        )
        if best.model == "double" and best.success:
            centers = sorted((best.parameters[3], best.parameters[6]))
            truth = sorted((c1, c2))
            error = max(abs(a - b) for a, b in zip(centers, truth, strict=True)) * 1000
        else:
            error = float("nan")
        rows.append({
            "case": name,
            "model": best.model,
            "center_error_mhz": error,
            "centers_accurate": bool(np.isfinite(error) and error <= args.tolerance_mhz),
            "bootstrap_width95_max_mhz": stability.bootstrap_width95_max_mhz,
            "bootstrap_successes": stability.bootstrap_successes,
            "bootstrap_trials": stability.bootstrap_trials,
            "multistart_range_max_mhz": stability.multistart_range_max_mhz,
            "multistart_successes": stability.multistart_successes,
            "multistart_trials": stability.multistart_trials,
        })
    output = location.output_dir / "center_stability.csv"
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    mlflow.set_tracking_uri(location.tracking_uri)
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=location.run_name) as active:
        mlflow.set_tags({
            "project": "MagnetIQ",
            "pipeline": "synthetic-center-stability",
            "git_revision": git_revision(),
            "quality_labels": "research-only",
        })
        mlflow.log_params({
            "seed": args.seed,
            "repeats": args.repeats,
            "bootstrap_trials": args.bootstrap,
            "multistart_trials": args.starts,
            "illustrative_center_tolerance_mhz": args.tolerance_mhz,
        })
        mlflow.log_metric("cases", float(len(rows)))
        mlflow.log_metric(
            "inaccurate_cases",
            float(sum(not bool(row["centers_accurate"]) for row in rows)),
        )
        mlflow.log_artifact(str(output), artifact_path="stability")
        print(f"MLflow run: {active.info.run_id}")
    print(f"Saved {len(rows)} synthetic cases: {output}")
    print("IID bootstrap is not a calibrated CI under structured residual mismatch.")


if __name__ == "__main__":
    main()
