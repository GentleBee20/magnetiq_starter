"""Research benchmark for continuous nuisance period and model-selection penalty."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.nuisance import fit_sinusoidal_nuisance
from magnetiq.processing.period_refinement import conservative_selection, refine_period
from magnetiq.processing.resonance import fit_spectrum
from scripts.benchmark_nuisance import center_error, make_cases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-seed", type=int, default=20261024)
    parser.add_argument("--test-seed", type=int, default=20261124)
    parser.add_argument("--repeats", type=int, default=6)
    parser.add_argument("--extra-penalty", type=float, default=8.0)
    parser.add_argument(
        "--output", type=Path, default=Path("reports/odmr/benchmarks/refined_period.csv")
    )
    args = parser.parse_args()
    if args.repeats < 1 or args.train_seed == args.test_seed or args.extra_penalty < 0:
        parser.error("Invalid repeats, seeds, or penalty")
    rows: list[dict[str, object]] = []
    for heldout, seed in ((False, args.train_seed), (True, args.test_seed)):
        for name, kind, c1, c2, freq, contrast in make_cases(seed, args.repeats, heldout):
            spectrum = OdmrSpectrum(name, tuple(freq), tuple(contrast))
            baseline = fit_spectrum(spectrum, 2)
            fixed = fit_sinusoidal_nuisance(spectrum, baseline)
            refined = refine_period(spectrum, baseline)
            truth = (c1, c2)
            baseline_error = center_error(
                [baseline.parameters[3], baseline.parameters[6]]
                if baseline.success and len(baseline.parameters) == 8
                else [],
                truth,
            )
            fixed_error = center_error(
                [fixed.parameters[3], fixed.parameters[6]] if fixed.success else [], truth
            )
            refined_error = center_error(
                [refined.parameters[3], refined.parameters[6]] if refined.success else [], truth
            )
            selected = conservative_selection(baseline, refined, extra_penalty=args.extra_penalty)
            rows.append(
                {
                    "split": "heldout" if heldout else "train",
                    "case": name,
                    "kind": kind,
                    "baseline_error_mhz": baseline_error,
                    "fixed_error_mhz": fixed_error,
                    "refined_error_mhz": refined_error,
                    "fixed_period_mhz": 1000 * fixed.period_ghz if fixed.period_ghz else None,
                    "refined_period_mhz": 1000 * refined.period_ghz if refined.period_ghz else None,
                    "baseline_aicc": baseline.aicc,
                    "refined_aicc": refined.aicc,
                    "selected": selected.selected,
                    "selected_error_mhz": refined_error
                    if selected.selected == "nuisance"
                    else baseline_error,
                }
            )
    if args.output.exists():
        parser.error(f"Refusing to overwrite existing output: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for split in ("train", "heldout"):
        for kind in ("clean", "oscillation_low", "oscillation_high"):
            group = [r for r in rows if r["split"] == split and r["kind"] == kind]
            means = {
                key: round(float(np.nanmean([float(r[key]) for r in group])), 5)
                for key in (
                    "baseline_error_mhz",
                    "fixed_error_mhz",
                    "refined_error_mhz",
                    "selected_error_mhz",
                )
            }
            print(
                split,
                kind,
                means,
                "nuisance selections:",
                sum(r["selected"] == "nuisance" for r in group),
            )
    print(f"Saved: {args.output}")
    print("Research only; AICc penalty is heuristic, not calibrated.")


if __name__ == "__main__":
    main()
