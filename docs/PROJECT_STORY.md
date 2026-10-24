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

## Held-out policy validation — implementation checkpoint

Implemented [the held-out protocol](HELDOUT_POLICY_VALIDATION.md): a separate
training seed selects a residual-error and correlation gate under a maximum
training false-failure rate; a second seed is evaluated only afterward.
Existing and previous-candidate policies are scored alongside the tuned gate,
with full per-case CSVs and immutable MLflow artifacts. The code remains
outside production QC. **No held-out measurements or results are claimed yet.**
The next milestone is to inspect its holdout performance and identify
whether successes persist under shifts in noise and distortion family.

## Held-out validation result — 24 October 2026

Run `ab2fe4ccc1674d78a2e2f2fe885d1fe5` (local MLflow), training
seed 20261024, held-out seed 20261124, 12 draws × 16 cases per split,
illustrative maximum center error 0.5 MHz. Thresholds selected **using
training cases only**: normalized RMSE > 0.10 AND absolute lag-1 residual
correlation > 0.985, applied only to existing REVIEW_REQUIRED cases.

| Held-out (192 rows; 178 accurate, 14 inaccurate) | Existing | Previous candidate | Tuned |
| --- | ---: | ---: | ---: |
| Accepted | 125 | 125 | 125 |
| Reviewed | 67 | 61 | 43 |
| Failed | 0 | 6 | 24 |
| Inaccurate correctly failed | 0/14 | 6/14 | 14/14 |
| Accurate incorrectly failed | 0/178 | 0/178 | 10/178 |
| Failure recall | 0% | 42.86% | 100% |
| False-failure rate | 0% | 0% | 5.62% |

Training split: 173 accurate, 19 inaccurate; tuned failure recall 19/19
(100%), false failures 4/173 (2.31%). The preselected training maximum
false-failure rate was 5%. **Held-out false failures 10/178 = 5.62%
exceeded that target**. All three policies showed zero accepted
inaccurate spectra in this synthetic set; the tuned policy preserves
FIT_OK cases rather than assessing those acceptances independently.

**Conclusion:** The tuned gate detects more inaccurate center estimates
but has measurable over-rejection, and the held-out false-failure rate
is above the nominal training constraint. Do **not** promote this policy
to production. Next: examine the ten false failures individually,
test shifts in distortion frequency and noise/SNR, use multiple
independent held-out seeds, and separately define model adequacy
versus center-estimation accuracy.

## Held-out per-case audit — false failures

Inspected the complete 192-row `holdout_cases.csv` for run
`ab2fe4ccc1674d78a2e2f2fe885d1fe5`.

- Exactly **14 inaccurate fits** (>0.5 MHz maximum center error) were
  flagged `FIT_FAILED`, and **10 accurate fits** (<=0.5 MHz) were also
  flagged `FIT_FAILED`. Another 125 accurate fits remained `FIT_OK`;
  43 accurate fits remained in review.
- All 24 failures occurred in the **oscillation** family. Among 12
  severity-1 oscillations, four were inaccurate and eight retained
  center accuracy; the tuned gate failed all 12. Among 12 severity-2
  oscillations, ten were inaccurate and two retained accuracy; the
  tuned gate again failed all 12.
- Example false failure: `000_oscillation_1` has 0.125 MHz maximum
  center error, nRMSE 0.114, |lag-1| 0.987. Example correct failure
  `005_oscillation_2` has 10.641 MHz center error, nRMSE 0.242,
  |lag-1| 0.993.
- The gate is therefore mostly detecting one strong structured-noise
  family, **not directly measuring parameter reliability**. Structured
  residuals can coexist with accurate centers.

**Next:** separate model-mismatch evidence from center-accuracy
conclusions; investigate extreme center misassignment, expand
stress tests beyond fixed sinusoidal perturbations, and evaluate
group-aware holdouts plus calibration of uncertainty estimates.
Production decisions are unchanged.

## Parameter-stability prototype — implementation checkpoint

Created [the parameter-stability protocol](PARAMETER_STABILITY.md):
a fixed-model residual bootstrap and jittered multi-start optimizer
analysis, with per-case comparison against known synthetic resonance
center truth and MLflow artifact tracking. This research layer aims to
test whether fitted-center stability helps separate accurate-but-poorly
modelled spectra from inaccurate center estimates. It deliberately does
not change production status rules. **No experimental benchmark
results or validated coverage claims have been recorded yet.**

## Center-stability audit — 24 October 2026

Analyzed the first nine-case synthetic center-stability CSV from local MLflow
run `a5603d3aac3e4db082121c88f00973ab`, seeded 20261124, 20 IID residual
bootstrap replicates and eight jittered optimizer restarts per case.
All 180 bootstrap refits and 72 restarts converged. By an *illustrative*
0.5 MHz maximum center-error tolerance, six spectra were accurate and three
were inaccurate.

| Case | Actual center error (MHz) | Bootstrap 95% full width (MHz) | Multi-start center range (MHz) |
| --- | ---: | ---: | ---: |
| 000_clean_0 | 0.015 | 0.020 | near zero |
| 000_oscillation_2 | 0.172 | 0.250 | 11.952 |
| 001_oscillation_2 | 2.227 | 0.569 | 5.313 |
| 002_oscillation_1 | 0.513 | 0.241 | 0.000012 |
| 002_oscillation_2 | 1.298 | 0.704 | 0.000112 |

**Key finding:** convergence and agreement across optimizer starts are not
evidence of center accuracy. The two inaccurate `002` cases show vanishingly
small multi-start ranges, whereas the accurate `000_oscillation_2` case
shows widely differing solutions. The bootstrap full interval widths are
not coverage probabilities or estimates of bias; IID residual resampling
is questionable in structured oscillatory residuals.

**Next:** inspect individual restart parameter vectors and objective values;
evaluate only near-optimal solutions rather than all converged ones, check for
peak permutations or pathological boundaries, and quantify bootstrap
coverage using larger synthetic, group-held-out datasets. Production QC
remains unchanged.

## Objective-aware restart and bootstrap coverage prototypes

Implemented additional experimental diagnostics:
- Per-restart center estimates, residual objective ratios, and proximity to
  parameter bounds (`restart_details.csv`).
- Multi-start center range restricted to solutions whose RSS is within a
  configurable ratio (default 1.01) of the selected fit.
- Per-resonance bootstrap percentile endpoints, and a separate seeded
  synthetic study estimating how frequently **both** intervals cover the
  known centers. The estimated joint coverage is descriptive, not a
  validated confidence guarantee.

See [Parameter Stability v2](PARAMETER_STABILITY_V2.md). No coverage
measurements or classification improvements have been claimed yet.
Production QC remains unchanged.

## Stability v2 and bootstrap coverage smoke results — 24 October 2026

Two research runs completed locally:
- Objective-aware restart analysis: MLflow run
  `523319d2816449718874bf000b9c54eb`, nine synthetic spectra,
  reporting `center_stability.csv` and restart details.
- IID residual bootstrap coverage: MLflow run
  `3c5a07aa186747c9acaf971863d6be15`, twelve of twelve spectra
  assessable, observed **joint empirical coverage 1/12 = 8.3%**.

The observed fraction means *both* known centers landed inside their
separate nominal 95% percentile intervals in only one spectrum. It is
not a claim that the combined region has a calibrated 95% coverage
target: marginal intervals and simultaneous coverage differ. Twelve
synthetic cases are insufficient for a robust population estimate, and
the cases reuse the same generator and correlated distortions.

**Next:** inspect the per-case coverage CSV and per-restart objectives,
distinguish clean from oscillatory failures, and estimate coverage with
more seeds and repetitions before attempting bootstrap variants or
changing production QC.
