"""Reproducible synthetic stress-test of candidate adequacy policy.

Run from repository root: python scripts/benchmark_adequacy.py
Synthetic labels represent constructed model mismatches, not actual hardware faults.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.adequacy import assess_candidate
from magnetiq.processing.diagnostics import diagnose_fit
from magnetiq.processing.resonance import evaluate_model, fit_spectrum


def main() -> None:
    """Evaluate current and candidate statuses on labelled synthetic examples."""
    rng = np.random.default_rng(20261024)
    frequency = np.linspace(2.85, 2.89, 401)
    parameters = np.array([1.0, 0.0, 0.04, 2.866, 0.0012, 0.03, 2.875, 0.0015])
    clean = evaluate_model(frequency, parameters, 2)
    noise = rng.normal(0.0, 0.0006, len(frequency))
    localized = 0.008 * np.exp(-(((frequency - 2.866) / 0.00045) ** 2))
    oscillation = 0.018 * np.sin((frequency - frequency[0]) * 2 * np.pi / 0.006)
    drift = 0.03 * ((frequency - frequency.mean()) / np.ptp(frequency)) ** 2
    cases = [
        ("clean", "adequate", clean + noise),
        ("local_mismatch", "review", clean + noise + localized),
        ("global_oscillation", "inadequate", clean + noise + oscillation),
        ("nonlinear_baseline", "inadequate", clean + noise + drift),
    ]
    output = Path("reports/odmr/benchmarks/adequacy_candidates.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for name, truth, values in cases:
        spectrum = OdmrSpectrum(name, tuple(frequency), tuple(values))
        fits = [fit_spectrum(spectrum, peaks) for peaks in (0, 1, 2)]
        diagnosis = diagnose_fit(spectrum, fits)
        candidate = assess_candidate(diagnosis)
        records.append(
            {
                "case": name,
                "synthetic_label": truth,
                "existing_status": diagnosis.status,
                "candidate_status": candidate.candidate_status,
                "normalized_rmse": diagnosis.normalized_rmse,
                "lag1_correlation": diagnosis.lag1_residual_correlation,
                "local_rmse_ratio": diagnosis.max_local_rmse_ratio,
                "candidate_reasons": ";".join(candidate.severe_reasons),
            }
        )
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    for row in records:
        print(
            f"{row['case']}: expected={row['synthetic_label']} "
            f"current={row['existing_status']} candidate={row['candidate_status']}"
        )
    print(f"Saved benchmark: {output}")
    print("CAUTION: four synthetic cases cannot calibrate operational thresholds.")


if __name__ == "__main__":
    main()
