"""Phase 2: stress-test sinusoidal nuisance fits against non-sinusoidal artifacts.

Run: python -m scripts.benchmark_robustness --repeats 6
No production QC is changed. Results are synthetic, not sensor calibration.
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
from magnetiq.processing.period_refinement import conservative_selection, refine_period
from magnetiq.processing.resonance import evaluate_model, fit_spectrum
from magnetiq.tracking import EXPERIMENT, git_revision, new_run_location
from scripts.benchmark_nuisance import center_error

KINDS = ("clean", "single_sine", "two_tone", "chirp", "harmonics", "curved_baseline")


def generate_cases(
    seed: int, repeats: int, *, shifted: bool
) -> list[tuple[str, str, float, float, np.ndarray, np.ndarray]]:
    """Make independently noisy cases with known ground-truth dip centers."""
    rng = np.random.default_rng(seed)
    x = np.linspace(2.85, 2.89, 401)
    t = x - x[0]
    cases: list[tuple[str, str, float, float, np.ndarray, np.ndarray]] = []
    for idx in range(repeats):
        c1, c2 = float(rng.uniform(2.862, 2.867)), float(rng.uniform(2.873, 2.879))
        params = np.array(
            [
                1.0,
                float(rng.uniform(-0.1, 0.1)),
                float(rng.uniform(0.025, 0.055)),
                c1,
                float(rng.uniform(0.0008, 0.0016)),
                float(rng.uniform(0.025, 0.055)),
                c2,
                float(rng.uniform(0.0008, 0.0016)),
            ]
        )
        clean = evaluate_model(x, params, 2)
        period = (0.0086 if shifted else 0.006) + float(rng.uniform(-0.0002, 0.0002))
        phase = float(rng.uniform(0.2, 2.8))
        a = 0.012 if shifted else 0.009
        for kind in KINDS:
            noise = rng.normal(0, 0.0006 if not shifted else 0.001, len(x))
            sine = np.sin(2 * np.pi * t / period + phase)
            if kind == "clean":
                artifact = np.zeros_like(x)
            elif kind == "single_sine":
                artifact = a * sine
            elif kind == "two_tone":
                artifact = a * (0.65 * sine + 0.6 * np.sin(2 * np.pi * t / (period * 0.57) + 0.4))
            elif kind == "chirp":
                phase_curve = (
                    2 * np.pi * (t / period + (0.28 if shifted else 0.15) * (t / period) ** 2)
                )
                artifact = a * np.sin(phase_curve + phase)
            elif kind == "harmonics":
                artifact = a * (sine + 0.4 * np.sin(4 * np.pi * t / period + phase)) / 1.4
            else:
                artifact = a * ((t - np.mean(t)) / np.ptp(t)) ** 2
            name = f"{'shift' if shifted else 'dev'}_{idx:03d}_{kind}"
            cases.append((name, kind, c1, c2, x, clean + artifact + noise))
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-seed", type=int, default=20261024)
    parser.add_argument("--test-seed", type=int, default=20271124)
    parser.add_argument("--repeats", type=int, default=6)
    parser.add_argument("--extra-penalty", type=float, default=8.0)
    parser.add_argument("--tolerance-mhz", type=float, default=0.5)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/odmr/experiments"))
    args = parser.parse_args()
    if args.repeats < 1 or args.extra_penalty < 0 or args.tolerance_mhz <= 0:
        parser.error("Invalid repeats, penalty or tolerance")
    if args.train_seed == args.test_seed:
        parser.error("Seeds must differ")

    rows: list[dict[str, object]] = []
    for shifted, seed in ((False, args.train_seed), (True, args.test_seed)):
        for name, kind, c1, c2, x, y in generate_cases(seed, args.repeats, shifted=shifted):
            spectrum = OdmrSpectrum(name, tuple(x), tuple(y))
            baseline = fit_spectrum(spectrum, 2)
            fixed = fit_sinusoidal_nuisance(spectrum, baseline)
            refined = refine_period(spectrum, baseline)
            truth = (c1, c2)
            be = center_error(
                list(baseline.parameters[i] for i in (3, 6)) if baseline.success else [], truth
            )
            fe = center_error(
                list(fixed.parameters[i] for i in (3, 6)) if fixed.success else [], truth
            )
            re = center_error(
                list(refined.parameters[i] for i in (3, 6)) if refined.success else [], truth
            )
            decision = conservative_selection(baseline, refined, extra_penalty=args.extra_penalty)
            se = re if decision.selected == "nuisance" else be
            rows.append(
                {
                    "case": name,
                    "split": "shifted" if shifted else "development",
                    "kind": kind,
                    "baseline_error_mhz": be,
                    "fixed_error_mhz": fe,
                    "refined_error_mhz": re,
                    "selected_error_mhz": se,
                    "selected_nuisance": decision.selected == "nuisance",
                    "baseline_within_tolerance": bool(np.isfinite(be) and be <= args.tolerance_mhz),
                    "selected_within_tolerance": bool(np.isfinite(se) and se <= args.tolerance_mhz),
                    "fixed_period_mhz": fixed.period_ghz * 1000
                    if fixed.period_ghz is not None
                    else None,
                    "refined_period_mhz": refined.period_ghz * 1000
                    if refined.period_ghz is not None
                    else None,
                    "baseline_rmse": baseline.rmse,
                    "refined_rmse": refined.rmse,
                }
            )

    summary: dict[str, dict[str, float]] = {}
    for split in ("development", "shifted"):
        for kind in KINDS:
            group = [r for r in rows if r["split"] == split and r["kind"] == kind]
            metric = {
                "n": float(len(group)),
                "baseline_mean_error_mhz": float(
                    np.nanmean(np.array([r["baseline_error_mhz"] for r in group], dtype=float))
                ),
                "refined_mean_error_mhz": float(
                    np.nanmean(np.array([r["refined_error_mhz"] for r in group], dtype=float))
                ),
                "selected_mean_error_mhz": float(
                    np.nanmean(np.array([r["selected_error_mhz"] for r in group], dtype=float))
                ),
                "nuisance_selected": float(sum(r["selected_nuisance"] is True for r in group)),
                "selected_inaccurate": float(
                    sum(r["selected_within_tolerance"] is False for r in group)
                ),
            }
            summary[f"{split}_{kind}"] = metric
            print(f"{split}/{kind}: {metric}")
    location = new_run_location(args.output_dir, "robustness-nonsinusoidal")
    output = location.output_dir / "robustness_cases.csv"
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (location.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    mlflow.set_tracking_uri(location.tracking_uri)
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=location.run_name) as active:
        mlflow.set_tags(
            {
                "project": "MagnetIQ",
                "pipeline": "synthetic-nonsinusoidal-robustness",
                "git_revision": git_revision(),
                "quality_labels": "research-only",
            }
        )
        mlflow.log_params(
            {
                "train_seed": args.train_seed,
                "test_seed": args.test_seed,
                "repeats": args.repeats,
                "extra_penalty": args.extra_penalty,
                "illustrative_tolerance_mhz": args.tolerance_mhz,
            }
        )
        mlflow.log_metric("cases", float(len(rows)))
        mlflow.log_artifacts(str(location.output_dir), artifact_path="robustness")
        print(f"MLflow run: {active.info.run_id}")
    print(f"Saved: {output}")
    print("Research only; synthetic results do not validate sensor accuracy.")


if __name__ == "__main__":
    main()
