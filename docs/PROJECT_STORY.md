# MagnetIQ — project narrative and evidence ledger

## The problem we started with

A successful nonlinear optimizer is **not** proof that an ODMR spectrum is
accurately described by its fitted model. A plausible orange curve can hide
systematic residuals near resonance. We built MagnetIQ to ask a narrower,
auditable question: **Can the selected spectral model be trusted enough for
further analysis, and what evidence argues against it?**

The project is a scientific computing and MLOps portfolio demonstration,
not a claim to have calibrated hardware, reconstructed 3D magnetic/current
maps, or diagnosed chip defects.

## What we built — chronological milestones

| Stage | Deliverable | Evidence or limitation |
| --- | --- | --- |
| 0. Data inventory | 105 spectra in a public Zenodo archive, grouped by acquisition folders | Dataset inventory; third-party raw ZIP is not committed |
| 1. Exploratory analysis | Overlay plots, range/noise proxies | Descriptive statistics only; not physical calibration |
| 2. Fitting baseline | Bounded baseline, one- and two-Lorentzian models, AICc selection | Successful optimization does not imply adequate line shape |
| 3. Diagnostics | Relative RMSE, lag-1 correlation, linewidth/edge checks | Provisional `FIT_OK`, `REVIEW_REQUIRED`, `FIT_FAILED` |
| 4. Local checks | Per-resonance RMSE and bias relative to off-resonance residuals | Flagged additional structured mismatches; no calibrated ground truth |
| 5. Reproducibility | Immutable experiment directories and MLflow tracking | Dataset SHA-256, Git revision and historical experiment comparison |
| 6. Explainable reporting | Observed values, provisional review limits and warning reasons in each plot | Validated visually on six measurements; table covers six numeric metrics, not every warning |
| 7. Candidate adequacy gate (current) | Separate `assess_candidate` and synthetic stress-test CLI | **Experimental proposal only**; production classifications unchanged |

## What we observed

- Across a previously compared set of 105 spectra, adding localized checks
  moved 21 cases from `FIT_OK` to `REVIEW_REQUIRED`, without changing
  the fitted parameters. That is **increased sensitivity**, not proven
  classification accuracy.
- Some conspicuously underfitted spectra still receive `REVIEW_REQUIRED`.
  The current production `FIT_FAILED` mainly tracks optimizer failure.
- A six-spectrum Fit Reporting v2 smoke test yielded four `FIT_OK` and
  two `REVIEW_REQUIRED`; plots explicitly displayed why.
- Real spectra do not currently have expert-labelled model-adequacy truth
  or uncertainty standards.

## What we are testing now

1. Define a **separate, auditable severe-model-mismatch gate**, without
   retroactively rewriting historical status decisions.
2. Construct synthetic cases with known injected local distortions,
   oscillations and nonlinear baselines, then record expected vs predicted
   behavior. The small initial cases are smoke tests, not calibration.
3. Examine false positives/negatives and difficult real-spectrum examples.
4. Compare candidate thresholds and diagnostic evidence in MLflow before
   selecting any production policy.

Run the first synthetic smoke benchmark:

```powershell
python scripts\benchmark_adequacy.py
```

Output: `reports/odmr/benchmarks/adequacy_candidates.csv`.

## Near-future scientific work

- Expand to a varied, seeded synthetic benchmark with held-out parameter
  regimes, noise amplitudes and multi-peak failure modes.
- Obtain independent expert adjudication or physical reference spectra;
  synthetic-only labels cannot establish experimental validity.
- Quantify uncertainty in fitted centers and linewidths (bootstrap/profile
  approaches), stability to initialization, and identifiability.
- Separate acquisition integrity, model adequacy, resonance detectability,
  and downstream physical interpretation into distinct QC dimensions.
- Only after independent validation should `FIT_FAILED` encompass
  converged-but-inadequate fits in the production pipeline.
- Longer-term magnetic-field/current reconstruction requires independent
  suitable spatially resolved data and physics-based validation.

## How to present the work

**Situation:** Quantum sensing analysis can produce superficially credible
fits without trustworthy evidence of model adequacy.

**Action:** Built a testable Python pipeline; compared physical line-shape
models, diagnosed residual structure, preserved MLflow experiments and made
per-spectrum decisions inspectable.

**Result:** Demonstrated reproducible fitting across 105 public spectra and
identified cases whose residual patterns warrant additional scrutiny. Not
yet a validated accuracy improvement.

**Next:** Calibrate severity decisions and quantify uncertainty with
synthetic challenges plus independently labelled reference measurements.

This document deliberately separates **completed evidence** from
**hypotheses** and **future commitments**.

## Benchmark checkpoint — 24 October 2026

The first four seeded synthetic cases passed all 35 engineering tests, but
**the experimental candidate status did not improve over existing QC**:

| Case | Expected demonstration label | Current | Candidate | nRMSE | Lag-1 | Local RMSE ratio |
| --- | --- | --- | --- | ---: | ---: | ---: |
| Clean | adequate | FIT_OK | FIT_OK | 0.014 | 0.058 | 0.942 |
| Local mismatch | review | FIT_OK | FIT_OK | 0.020 | 0.328 | 1.915 |
| Global oscillation | inadequate | REVIEW_REQUIRED | REVIEW_REQUIRED | 0.150 | 0.991 | 0.458 |
| Nonlinear baseline | inadequate | REVIEW_REQUIRED | REVIEW_REQUIRED | 0.028 | 0.818 | 0.814 |

**Interpretation:** the candidate hard gate requires nRMSE > 0.20 plus a
second severe signal, so high residual correlation alone never produces a
failure. Localized mismatch fell just below the review ratio of 2.0. An
artificially imposed label of `inadequate` is a hypothesis, not proof of
unacceptable resonance parameter accuracy. The local noise denominator can
also be inflated by structured off-resonance residuals.

**Next decision:** define a fit-failure *target* (for example, error in
estimated resonance center relative to an explicitly declared tolerance),
then build a seeded multi-severity benchmark with separate labels for
model mismatch, parameter accuracy, and optimizer convergence. Report
confusion matrices and abstention/review rates on held-out cases; compare
candidate policies without modifying historical production labels.

## Ground-truth benchmarking milestone (implementation pending local validation)

Added `scripts/benchmark_ground_truth.py` and
[`docs/GROUND_TRUTH_BENCHMARK.md`](GROUND_TRUTH_BENCHMARK.md).
The seeded experiment evaluates known synthetic resonance-center errors across
noise, localized distortions, oscillations and curved baselines, rather than
assuming that every intentionally distorted trace must be classified failed.
It compares current and candidate policies via false-acceptance and
false-failure rates. **No results have been collected or validated yet.**
The next steps are to run the benchmark, inspect difficult cases, evaluate
held-out seeds, and then track validated comparisons in MLflow.

## Ground-truth benchmark result — 24 October 2026

The user executed the seeded 12-draw benchmark locally with 192 synthetic
rows and an **illustrative** maximum-center-error tolerance of 0.5 MHz.
Ruff lint and formatting, mypy, and all 38 tests passed.

| Measure | Existing QC | Experimental candidate |
| --- | ---: | ---: |
| FIT_OK | 124/192 | 124/192 |
| REVIEW_REQUIRED | 68/192 | 65/192 |
| FIT_FAILED | 0/192 | 3/192 |
| False-accept rate given inaccurate centers | 0 | 0 |
| False-failure rate given accurate centers | 0 | 0 |

Of 192 generated rows, **173** had two resonance centers estimated within
0.5 MHz, and **19** did not. The candidate policy reassigned three reviewed
rows to failed; it did not change the number of accepted rows. The
aggregate output alone does **not** reveal whether all three failed rows
are among the 19 inaccurate ones, nor the full status × accuracy matrix;
inspect the detailed CSV before claiming that result.

**Limits:** 0.5 MHz is not a measured instrument requirement, the same
noise is reused within parameter draws, and zero-distortion cases repeat
within each family. This is a development benchmark, not an independent
held-out experimental validation. Its results are not a basis for a
production failure threshold.

**Next:** Produce per-policy status × parameter-accuracy contingency
tables; inspect the 19 inaccurate rows; test alternative held-out seeds
and tolerances; then integrate comparative metrics with MLflow.

## Per-case CSV audit — 192-row seed 20261024 benchmark

The complete locally generated CSV was inspected, resolving the contingency
table left open in the aggregate benchmark checkpoint:

| Ground truth (0.5 MHz illustrative tolerance) | Existing FIT_OK | Existing REVIEW | Candidate FIT_OK | Candidate REVIEW | Candidate FAILED |
| --- | ---: | ---: | ---: | ---: | ---: |
| Accurate (173) | 124 | 49 | 124 | 49 | 0 |
| Inaccurate (19) | 0 | 19 | 0 | 16 | 3 |

Every inaccurate result came from **oscillatory contamination**: 7 of 12
at severity 1, and 12 of 12 at severity 2. None of the other distortion
families exceeded the center-error tolerance in this seeded grid. The
candidate gate therefore caught **3/19 = 15.8%** of inaccurate cases as
`FIT_FAILED`; the remainder correctly avoided `FIT_OK` but stayed
`REVIEW_REQUIRED`. None of the 173 accurate cases were failed.

One example (`002_oscillation_2`) had the *largest* center error,
1.981 MHz, yet remained `REVIEW_REQUIRED` because relative RMSE was
0.189, below the candidate's 0.20 global-error threshold.
All 19 inaccurate cases exhibited high lag-1 residual correlation
(approximately 0.986–0.992). This is evidence of a poorly calibrated
severity ranking for this distortion family; it is not proof that a
standalone correlation threshold generalizes to measured spectra.

**Next research experiment:** evaluate center-error sensitivity versus
false-failure rate across explicitly selected residual-correlation and
global-error gates on **held-out synthetic parameter/noise/distorion
regimes**, with confidence intervals and distinct model-adequacy and
center-accuracy outcomes. Do not change production QC yet.
