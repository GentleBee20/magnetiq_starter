# Ground-truth fit-adequacy benchmark (experimental)

The original ODMR dataset has no verified center-truth labels. This benchmark
therefore generates seeded synthetic spectra with *known Lorentzian centers*.
It measures a concrete downstream parameter-quality outcome separately from
visual model mismatch and optimization convergence.

## Commands

```powershell
python scripts\benchmark_ground_truth.py --seed 20261024 --repeats 12 --tolerance-mhz 0.5
```

Default 12 parameter draws × 4 distortion families × 4 strengths = **192**
examples. Noise/clean baseline is fixed across distortions for each draw to
support paired comparisons. Relative to a standard 401-point spectral sweep,
the 0.5 MHz tolerance is **illustrative**, NOT derived from experimental
requirements. The command intentionally refuses overwriting an existing CSV.

Each row contains true dip centers, largest estimated-center error (MHz),
a boolean tolerance outcome, production status, candidate status, and
diagnostic scores. Missing fitted centers count as inaccurate.

The terminal comparison reports:
- accept/review/failure rates,
- false acceptance **conditional on inaccurate center estimation**,
- false failure **conditional on accurate center estimation**.

These operational labels are *not* equivalent to classifying the injected
distortion family. A distorted spectrum may still yield accurate centers,
while an otherwise clean spectrum may produce inaccurate centers.

## Scientific limitations and next work

- Synthetic truth is not hardware truth or calibrated sensor accuracy.
- Duplicated zero-severity variants within each draw are not independent
  samples; do not claim 192 independent acquisition conditions.
- This initial grid is useful for debugging, not a statistically valid held-out
  classifier evaluation. Threshold tuning on these same draws would overfit.
- Model selection may choose baseline or single resonance, in which case
  two-center accuracy cannot be established.
- Expand to held-out seeds, varied SNR/separation/linewidth regimes and
  independent reference measurements.
- Add MLflow logging and bootstrap uncertainty *after* verifying the
  benchmark's metrics and chosen center-error tolerance.

The production `FIT_FAILED` definition is unchanged.
