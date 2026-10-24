"""Compare Lorentzian versus sinusoidal nuisance on seeded shifted regimes.

Run: python -m scripts.benchmark_nuisance
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import mlflow
import numpy as np

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.nuisance import fit_sinusoidal_nuisance
from magnetiq.processing.resonance import evaluate_model, fit_spectrum
from magnetiq.tracking import EXPERIMENT, git_revision, new_run_location


def make_cases(
    seed: int, repeats: int, heldout: bool
) -> list[tuple[str, str, float, float, np.ndarray, np.ndarray]]:
    """Independent latent draws; heldout shifts periods and phases."""
    rng = np.random.default_rng(seed)
    frequency = np.linspace(2.85, 2.89, 401)
    periods = (0.0051, 0.0072, 0.0086) if heldout else (0.005, 0.006, 0.008)
    phases = (0.42, 1.37, 2.54) if heldout else (0.0, 0.9, 1.8)
    cases: list[tuple[str, str, float, float, np.ndarray, np.ndarray]] = []
    for index in range(repeats):
        c1 = float(rng.uniform(2.862, 2.867))
        c2 = float(rng.uniform(2.873, 2.879))
        params = np.array([
            1.0, float(rng.uniform(-0.1, 0.1)),
            float(rng.uniform(0.025, 0.055)), c1, float(rng.uniform(0.0008, 0.0016)),
            float(rng.uniform(0.025, 0.055)), c2, float(rng.uniform(0.0008, 0.0016)),
        ])
        clean = evaluate_model(frequency, params, 2)
        for kind in ("clean", "oscillation_low", "oscillation_high"):
            noise = rng.normal(0, 0.0006, len(frequency))
            contamination = np.zeros_like(frequency)
            if kind != "clean":
                amplitude = 0.006 if kind == "oscillation_low" else 0.012
                contamination = amplitude * np.sin(
                    2 * np.pi * (frequency - frequency[0]) / periods[index % 3]
                    + phases[index % 3]
                )
            name = f"{'heldout' if heldout else 'train'}_{index:03d}_{kind}"
            cases.append((name, kind, c1, c2, frequency, clean + noise + contamination))
    return cases


def center_error(centers: list[float], truth: tuple[float, float]) -> float:
    """Maximum matching error between sorted center pairs in MHz."""
    if len(centers) != 2 or not np.all(np.isfinite(centers)):
        return float("nan")
    return float(
        max(abs(a - b) for a, b in zip(sorted(centers), sorted(truth), strict=True)) * 1000
    )


def summarize(rows: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    """Compare center errors rather than equating lower RSS with correctness."""
    out: dict[str, dict[str, float]] = {}
    for split in ("train", "heldout"):
        for kind in ("clean", "oscillation_low", "oscillation_high"):
            group = [r for r in rows if r["split"] == split and r["kind"] == kind]
            if group:
                out[f"{split}_{kind}"] = {
                    "n": float(len(group)),
                    "baseline_mean_error_mhz": float(np.nanmean(
                        np.asarray([r["baseline_error_mhz"] for r in group], dtype=float)
                    )),
                    "nuisance_mean_error_mhz": float(np.nanmean(
                        np.asarray([r["nuisance_error_mhz"] for r in group], dtype=float)
                    )),
                    "selected_mean_error_mhz": float(np.nanmean(
                        np.asarray([r["selected_error_mhz"] for r in group], dtype=float)
                    )),
                    "nuisance_selected": float(sum(bool(r["select_nuisance"]) for r in group)),
                }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-seed", type=int, default=20261024)
    parser.add_argument("--test-seed", type=int, default=20261124)
    parser.add_argument("--repeats", type=int, default=6)
    parser.add_argument("--tolerance-mhz", type=float, default=0.5)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/odmr/experiments"))
    args = parser.parse_args()
    if args.repeats < 1 or args.tolerance_mhz <= 0 or args.train_seed == args.test_seed:
        parser.error("Require positive repeats/tolerance and different seeds")
    rows: list[dict[str, object]] = []
    for heldout, seed in ((False, args.train_seed), (True, args.test_seed)):
        for name, kind, c1, c2, frequency, contrast in make_cases(seed, args.repeats, heldout):
            spectrum = OdmrSpectrum(name, tuple(frequency), tuple(contrast))
            baseline = fit_spectrum(spectrum, 2)
            nuisance = fit_sinusoidal_nuisance(spectrum, baseline)
            baseline_error = center_error(
                [baseline.parameters[3], baseline.parameters[6]]
                if baseline.success and len(baseline.parameters) == 8 else [], (c1, c2)
            )
            nuisance_error = center_error(
                [nuisance.parameters[3], nuisance.parameters[6]]
                if nuisance.success else [], (c1, c2)
            )
            selected = bool(nuisance.success and nuisance.aicc < baseline.aicc)
            selected_error = nuisance_error if selected else baseline_error
            rows.append({
                "case": name, "split": "heldout" if heldout else "train", "kind": kind,
                "truth_1_ghz": c1, "truth_2_ghz": c2,
                "baseline_error_mhz": baseline_error, "nuisance_error_mhz": nuisance_error,
                "selected_error_mhz": selected_error, "select_nuisance": selected,
                "baseline_accurate": bool(np.isfinite(baseline_error) and baseline_error <= args.tolerance_mhz),
                "nuisance_accurate": bool(np.isfinite(nuisance_error) and nuisance_error <= args.tolerance_mhz),
                "selected_accurate": bool(np.isfinite(selected_error) and selected_error <= args.tolerance_mhz),
                "baseline_aicc": baseline.aicc, "nuisance_aicc": nuisance.aicc,
                "baseline_rmse": baseline.rmse, "nuisance_rmse": nuisance.rmse,
                "nuisance_period_ghz": nuisance.period_ghz,
                "nuisance_amplitude": nuisance.amplitude,
            })
    location = new_run_location(args.output_dir, "sinusoidal-nuisance-research")
    output = location.output_dir / "nuisance_comparison.csv"
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = summarize(rows)
    (location.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    mlflow.set_tracking_uri(location.tracking_uri)
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=location.run_name) as active:
        mlflow.set_tags({
            "project": "MagnetIQ", "pipeline": "synthetic-sinusoidal-nuisance",
            "git_revision": git_revision(), "quality_labels": "research-only",
        })
        mlflow.log_params({
            "train_seed": args.train_seed, "test_seed": args.test_seed,
            "repeats": args.repeats, "center_tolerance_mhz": args.tolerance_mhz,
            "period_grid_ghz": "0.004,0.005,0.006,0.007,0.008,0.009",
        })
        mlflow.log_metric("cases", float(len(rows)))
        mlflow.log_artifacts(str(location.output_dir), artifact_path="nuisance")
        print(f"MLflow run: {active.info.run_id}")
    print(f"Saved: {output}")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("AICc ignores grid search multiplicity; research-only, no production changes.")


if __name__ == "__main__":
    main()
