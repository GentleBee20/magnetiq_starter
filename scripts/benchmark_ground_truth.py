"""Seeded ODMR benchmark with known center truth and held-out synthetic cases.

Run: python scripts/benchmark_ground_truth.py
These are synthetic model-stress experiments, not sensor calibration.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.adequacy import assess_candidate
from magnetiq.processing.diagnostics import diagnose_fit
from magnetiq.processing.resonance import evaluate_model, fit_spectrum


def make_cases(seed: int, repeats: int) -> list[tuple[str, float, float, np.ndarray, np.ndarray]]:
    """Generate reproducible measurements with two known physical dip centers."""
    rng = np.random.default_rng(seed)
    frequency = np.linspace(2.85, 2.89, 401)
    cases = []
    for index in range(repeats):
        center_1 = float(rng.uniform(2.862, 2.867))
        center_2 = float(rng.uniform(2.873, 2.879))
        parameters = np.array(
            [
                1.0,
                0.0,
                rng.uniform(0.025, 0.055),
                center_1,
                rng.uniform(0.0008, 0.0016),
                rng.uniform(0.025, 0.055),
                center_2,
                rng.uniform(0.0008, 0.0016),
            ]
        )
        clean = evaluate_model(frequency, parameters, 2)
        baseline_noise = rng.normal(0, 0.0006, len(frequency))
        for kind in ("clean", "localized", "oscillation", "curved_baseline"):
            for severity in (0.0, 0.5, 1.0, 2.0):
                distortion = np.zeros_like(frequency)
                if kind == "localized":
                    distortion = (
                        severity * 0.005 * np.exp(-(((frequency - center_1) / 0.0005) ** 2))
                    )
                elif kind == "oscillation":
                    distortion = (
                        severity * 0.012 * np.sin((frequency - frequency[0]) * 2 * np.pi / 0.006)
                    )
                elif kind == "curved_baseline":
                    distortion = (
                        severity
                        * 0.025
                        * (((frequency - frequency.mean()) / np.ptp(frequency)) ** 2)
                    )
                name = f"{index:03d}_{kind}_{severity:g}"
                cases.append(
                    (name, center_1, center_2, frequency, clean + baseline_noise + distortion)
                )
    return cases


def evaluate(
    cases: list[tuple[str, float, float, np.ndarray, np.ndarray]],
    tolerance_mhz: float,
) -> list[dict[str, object]]:
    """Evaluate best fit's center error against construction truth."""
    rows: list[dict[str, object]] = []
    for name, center_1, center_2, frequency, contrast in cases:
        spectrum = OdmrSpectrum(name, tuple(frequency), tuple(contrast))
        fits = [fit_spectrum(spectrum, peaks) for peaks in (0, 1, 2)]
        diagnostic = diagnose_fit(spectrum, fits)
        candidate = assess_candidate(diagnostic)
        centers = [v for v in (diagnostic.center_1_ghz, diagnostic.center_2_ghz) if v is not None]
        if len(centers) == 2:
            estimated = sorted(centers)
            truth = sorted((center_1, center_2))
            maximum_error_mhz = (
                max(abs(a - b) for a, b in zip(estimated, truth, strict=True)) * 1000
            )
        else:
            maximum_error_mhz = float("nan")
        accurate = bool(np.isfinite(maximum_error_mhz) and maximum_error_mhz <= tolerance_mhz)
        rows.append(
            {
                "case": name,
                "distortion": name.split("_", 1)[1].rsplit("_", 1)[0],
                "severity": float(name.rsplit("_", 1)[1]),
                "center_truth_1_ghz": center_1,
                "center_truth_2_ghz": center_2,
                "max_center_error_mhz": maximum_error_mhz,
                "centers_within_tolerance": accurate,
                "tolerance_mhz": tolerance_mhz,
                "current_status": diagnostic.status,
                "candidate_status": candidate.candidate_status,
                "normalized_rmse": diagnostic.normalized_rmse,
                "abs_lag1": abs(diagnostic.lag1_residual_correlation),
                "max_local_rmse_ratio": diagnostic.max_local_rmse_ratio,
                "warnings": ";".join(diagnostic.warnings),
            }
        )
    return rows


def performance(rows: list[dict[str, object]], status_key: str) -> dict[str, float]:
    """Rates across known-accurate and known-inaccurate synthetic cases."""
    accurate = [row for row in rows if row["centers_within_tolerance"]]
    inaccurate = [row for row in rows if not row["centers_within_tolerance"]]
    return {
        "count": float(len(rows)),
        "accept_rate": sum(r[status_key] == "FIT_OK" for r in rows) / len(rows),
        "review_rate": sum(r[status_key] == "REVIEW_REQUIRED" for r in rows) / len(rows),
        "failed_rate": sum(r[status_key] == "FIT_FAILED" for r in rows) / len(rows),
        "false_accept_given_inaccurate": (
            sum(r[status_key] == "FIT_OK" for r in inaccurate) / len(inaccurate)
            if inaccurate
            else float("nan")
        ),
        "false_failure_given_accurate": (
            sum(r[status_key] == "FIT_FAILED" for r in accurate) / len(accurate)
            if accurate
            else float("nan")
        ),
        "inaccurate_count": float(len(inaccurate)),
        "accurate_count": float(len(accurate)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--tolerance-mhz", type=float, default=0.5)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/odmr/benchmarks"))
    args = parser.parse_args()
    if args.repeats < 1 or args.tolerance_mhz <= 0:
        parser.error("repeats must be >= 1 and tolerance-mhz must be positive")
    rows = evaluate(make_cases(args.seed, args.repeats), args.tolerance_mhz)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / f"ground_truth_seed{args.seed}_n{args.repeats}.csv"
    if path.exists():
        parser.error(f"Refusing to overwrite existing benchmark: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} labelled synthetic cases: {path}")
    for label, key in (("Existing", "current_status"), ("Candidate", "candidate_status")):
        print(f"{label} policy:")
        for metric, value in performance(rows, key).items():
            print(f"  {metric}: {value:.4g}")
    print("WARNING: 0.5 MHz is an illustrative tolerance, not an instrument specification.")
    print("Synthetic performance is not evidence of experimental hardware accuracy.")


if __name__ == "__main__":
    main()
