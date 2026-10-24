"""Seeded marginal and joint bootstrap coverage calibration study.

Run as a module from the repository root.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import mlflow
import numpy as np

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.diagnostics import choose_fit
from magnetiq.processing.resonance import fit_spectrum
from magnetiq.processing.stability import center_stability
from magnetiq.tracking import EXPERIMENT, git_revision, new_run_location
from scripts.benchmark_ground_truth import make_cases


def summarize(rows: list[dict[str, object]]) -> dict[str, float]:
    """Coverage denominators include only spectra with two assessable intervals."""
    assessed = [row for row in rows if row["assessable"]]
    if not assessed:
        return {
            "assessable": 0.0,
            "coverage_center_1": float("nan"),
            "coverage_center_2": float("nan"),
            "joint_coverage": float("nan"),
        }
    return {
        "assessable": float(len(assessed)),
        "coverage_center_1": sum(bool(row["covered_1"]) for row in assessed) / len(assessed),
        "coverage_center_2": sum(bool(row["covered_2"]) for row in assessed) / len(assessed),
        "joint_coverage": sum(bool(row["joint_covered"]) for row in assessed) / len(assessed),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[20261224, 20261225])
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--bootstrap", type=int, default=100)
    parser.add_argument("--starts", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/odmr/experiments"))
    args = parser.parse_args()
    if min(args.repeats, args.bootstrap, args.starts) < 1:
        parser.error("Trial counts must be positive")
    if len(set(args.seeds)) != len(args.seeds):
        parser.error("Seeds must be distinct")
    rows: list[dict[str, object]] = []
    for seed in args.seeds:
        selected = [
            case
            for case in make_cases(seed, args.repeats)
            if case[0].endswith(("clean_0", "oscillation_1", "oscillation_2"))
        ]
        for case_index, (name, center_1, center_2, freq, contrast) in enumerate(selected):
            spectrum = OdmrSpectrum(name, tuple(freq), tuple(contrast))
            chosen = choose_fit([fit_spectrum(spectrum, order) for order in (0, 1, 2)])
            truth = sorted((center_1, center_2))
            family = "clean" if "_clean_" in name else "oscillation"
            for method in ("residual_raw", "residual_centered", "gaussian_known_noise"):
                centered = method == "residual_centered"
                stability = center_stability(
                    spectrum,
                    chosen,
                    seed=seed + case_index,
                    bootstrap_trials=args.bootstrap,
                    multistart_trials=args.starts,
                    center_residuals=centered,
                    gaussian_noise_std=0.0006 if method == "gaussian_known_noise" else None,
                )
                one = stability.bootstrap_interval_1_ghz
                two = stability.bootstrap_interval_2_ghz
                assessable = one is not None and two is not None
                covered_1 = bool(one is not None and one[0] <= truth[0] <= one[1])
                covered_2 = bool(two is not None and two[0] <= truth[1] <= two[1])
                estimates = (
                    sorted((chosen.parameters[3], chosen.parameters[6]))
                    if chosen.model == "double" and chosen.success
                    else [float("nan")] * 2
                )
                rows.append(
                    {
                        "method": method,
                        "truth_1_ghz": truth[0],
                        "truth_2_ghz": truth[1],
                        "estimated_1_ghz": estimates[0],
                        "estimated_2_ghz": estimates[1],
                        "error_1_mhz": (estimates[0] - truth[0]) * 1000,
                        "error_2_mhz": (estimates[1] - truth[1]) * 1000,
                        "interval_1_low_ghz": one[0] if one else None,
                        "interval_1_high_ghz": one[1] if one else None,
                        "interval_2_low_ghz": two[0] if two else None,
                        "interval_2_high_ghz": two[1] if two else None,
                        "width_1_mhz": (one[1] - one[0]) * 1000 if one else None,
                        "width_2_mhz": (two[1] - two[0]) * 1000 if two else None,
                        "fitted_width_1_mhz": chosen.parameters[4] * 1000
                        if len(chosen.parameters) == 8
                        else None,
                        "fitted_width_2_mhz": chosen.parameters[7] * 1000
                        if len(chosen.parameters) == 8
                        else None,
                        "seed": seed,
                        "case": name,
                        "family": family,
                        "centered_residuals": centered,
                        "model": chosen.model,
                        "assessable": assessable,
                        "covered_1": covered_1 if assessable else None,
                        "covered_2": covered_2 if assessable else None,
                        "joint_covered": covered_1 and covered_2 if assessable else None,
                        "bootstrap_successes": stability.bootstrap_successes,
                        "bootstrap_trials": stability.bootstrap_trials,
                    }
                )
    location = new_run_location(args.output_dir, "bootstrap-calibration")
    output = location.output_dir / "bootstrap_calibration.csv"
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary: dict[str, dict[str, float]] = {}
    mlflow.set_tracking_uri(location.tracking_uri)
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=location.run_name) as active:
        mlflow.set_tags(
            {
                "project": "MagnetIQ",
                "pipeline": "synthetic-bootstrap-calibration",
                "git_revision": git_revision(),
                "quality_labels": "research-only",
            }
        )
        mlflow.log_params(
            {
                "seeds": ",".join(map(str, args.seeds)),
                "repeats": args.repeats,
                "bootstrap_trials": args.bootstrap,
                "starts": args.starts,
            }
        )
        for family in ("clean", "oscillation"):
            for method in ("residual_raw", "residual_centered", "gaussian_known_noise"):
                group = [row for row in rows if row["family"] == family and row["method"] == method]
                label = f"{family}_{method}"
                metrics = summarize(group)
                summary[label] = metrics
                for name, value in metrics.items():
                    if np.isfinite(value):
                        mlflow.log_metric(f"{label}_{name}", value)
                print(f"{label}: {metrics}")
        (location.output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
        mlflow.log_artifacts(str(location.output_dir), artifact_path="calibration")
        print(f"MLflow run: {active.info.run_id}")
    print(f"Saved: {output}")
    print("These are marginal percentile intervals, NOT guaranteed calibrated coverage.")


if __name__ == "__main__":
    main()
