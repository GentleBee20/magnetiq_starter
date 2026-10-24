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

## Stability v2 detailed CSV audit — 24 October 2026

Analyzed the three user-supplied local run artifacts `center_stability.csv`,
`restart_details.csv` and `bootstrap_coverage.csv`.

**Restart objectives:** 72 of 72 attempts converged; 67/72 met
RSS <= 1.01 times the reference RSS; no solutions were flagged near
parameter bounds. For `000_oscillation_2`, full-restart center range
was 11.952 MHz while six near-optimal starts spanned only
0.00000135 MHz; the two worse starts had RSS ratios 1.321 and 1.326.
For `001_oscillation_2`, full-restart range 5.313 MHz became
0.0000374 MHz across five near-optimal starts; three worse starts
had RSS ratios 1.015, 1.052 and 1.015.

**Stable is not accurate:** `001_oscillation_2` nevertheless has
2.227 MHz maximum center error. `002_oscillation_2` has 1.298 MHz
error despite all eight restarts converging to nearly identical
center estimates (range about 0.000112 MHz).

**Bootstrap joint coverage:** 1/4 clean cases, 0/8 oscillatory cases;
1/12 overall. Thus even clean spectra failed joint coverage in this
very small smoke test. This cannot be assigned solely to correlated
residuals without further diagnosis. Nominal marginal 95% intervals do
not imply exact 95% joint coverage, and 20 replicates per spectrum are
too few for reliable percentile estimation.

**Next:** independently evaluate marginal coverage for each resonance,
try substantially more bootstrap replicates, test residual-centering
and sampling assumptions, and assess uncertainty calibration over
many independent draws and shifted noise/distortion regimes. Do not
promote bootstrap widths or restart stability to production accuracy
claims.

## Bootstrap calibration study — implementation checkpoint

Added a reproducible multiple-seed comparison of **marginal coverage for
each resonance** and **joint coverage for both**, using 100 bootstrap refits
per spectrum by default. It compares the original residual bootstrap to
mean-centered residual resampling on the same synthetic cases, preserves
all outputs in a new MLflow run, and keeps the existing production QC
rules unchanged.

This is an **experiment proposal implemented in code**, not a claim of
successful calibration. The independent seeds still share the same
synthetic generator and line-shape assumptions. Evaluate empirical
coverage, failure-to-assess frequency, and differences between clean and
oscillatory cases before proposing another uncertainty method.

## Bootstrap calibration checkpoint — 24 October 2026

Two local MLflow bootstrap-calibration runs compared raw versus
mean-centered IID residual resampling.

**Pilot** (seeds 20261224, 20261225, two draws per seed, 50 replicates):
- Clean (n=4): center 1 coverage 1/4, center 2 4/4, joint 1/4.
- Oscillation (n=8): center 1 coverage 3/8, center 2 0/8,
  joint 0/8.
- Raw and centered methods had identical inclusion outcomes.

**Larger exploratory run** (seeds 20261224–20261226, four draws
per seed, 100 replicates, MLflow run
`fa6c366c4ae2451b9355b50b08ece51f`):
- Clean (n=12): center 1 coverage **8/12 (66.7%)**;
  center 2 **12/12 (100%)**; joint **8/12 (66.7%)**.
- Oscillatory (n=24): center 1 **6/24 (25%)**;
  center 2 **4/24 (16.7%)**; joint **0/24**.
- Residual centering had **no change in coverage counts** for either
  family; this does not imply identical numerical intervals. A model
  with a fitted constant baseline can absorb a residual mean shift.

These are marginal 95% percentile intervals combined into an
uncalibrated joint-coverage check. The generator reuses latent
parameters and noise within each seed/draw, so the 24 oscillatory
conditions are not 24 independent draws. The nominal 95% level
should not be used as an exact joint-coverage target. The low
coverage warrants more research, **not a claim of calibrated
uncertainty or a production failure rule**.

**Next:** diagnose center-1 versus center-2 bias with per-case
truth, point estimates, and interval endpoints; run a parametric
bootstrap using the known independent Gaussian noise model as a
correct-specification control; then test structured-noise
strategies under held-out noise and oscillation regimes.

## Per-case bootstrap calibration CSV audit

The uploaded 72-row `bootstrap_calibration.csv` contains 36 distinct
synthetic spectra, each evaluated twice (raw and centered residuals).
The supplied `summary.json` agrees with recomputed coverage counts.
All bootstrap runs were assessable with 100/100 successful replicates.

- Clean: center 1 covered 8/12; center 2 12/12; both 8/12.
  The four clean center-1 misses were seed 20261224, cases 000/001/003,
  and seed 20261225, case 001. All four clean cases from seed 20261226
  covered both centers.
- Oscillatory: center 1 covered 6/24; center 2 covered 4/24; both 0/24.
- Raw and centered bootstrap made identical inclusion decisions on every
  paired case; interval *bounds* were not logged, so numerical equality
  of intervals cannot be asserted.

**Limitation found in the artifact schema:** the per-case CSV has coverage
booleans but omits true/estimated centers, interval endpoints, widths
and resonance parameters. Therefore these artifacts do not identify
whether clean center-1 misses are due to systematic bias or intervals
that are too narrow. Next step: add diagnostic endpoints and
per-case errors to the benchmark, then compare IID residual bootstrap
with a Gaussian-noise parametric control using a larger grouped
synthetic validation design. Do not tune production thresholds yet.

## Calibrating uncertainty: diagnostic exports and parametric control

Implemented a research-only extension of the bootstrap calibration study.
The CSV now includes synthetic true and estimated resonance centers,
signed center errors, per-center percentile interval endpoints/widths,
and fitted linewidths. Added a **known Gaussian-noise scale**
(`sigma = 0.0006` normalized contrast units) parametric-bootstrap arm
beside raw and mean-centered residual resampling. The synthetic clean
generator uses this Gaussian baseline-noise scale, so the parametric
arm is a useful clean-case control. It remains **model-misspecified**
for the oscillatory cases, where the signal contains an extra coherent
distortion. Per-center marginal coverage and joint coverage continue
to be scored separately. Experiments are immutable MLflow runs; no
production QC thresholds changed. The implementation requires new
test and empirical execution before claims about calibration.

## Known-Gaussian-noise bootstrap control — 24 October 2026

Both local calibration runs succeeded. The larger study used seeds
20261224–20261226, four latent-parameter draws per seed (12 clean
spectra plus 24 oscillatory conditions), 100 resamples per case.
MLflow run: `d395e37b2161491cb31b44158481fcd3`.

| Arm | Clean joint coverage | Oscillatory joint coverage |
| --- | ---: | ---: |
| Raw residual | 8/12 (66.7%) | 0/24 |
| Mean-centered residual | 8/12 (66.7%) | 0/24 |
| Known-noise parametric Gaussian | 10/12 (83.3%) | 0/24 |

Marginal clean Gaussian coverage: center 1 10/12, center 2 12/12.
Oscillatory Gaussian marginal coverage: center 1 0/24, center 2 0/24.
The smaller pilot (two seeds, two draws each, 50 resamples) likewise
showed clean Gaussian joint coverage 2/4 vs residual 1/4, and 0/8
oscillatory coverage for all three arms; the pilot overlaps with the
larger run and is not an independent confirmation.

**Interpretation:** specifying the correct synthetic baseline-noise
scale helps clean-data interval coverage, while pure Gaussian
perturbations do not account for coherent oscillatory mismatch.
Neither marginal percentile intervals nor their intersection are a
calibrated joint confidence region; there are few independent latent
draws. No production QC changes.

**Next:** audit exact center estimates, signed errors and interval
endpoints in the richer calibration CSV; assess bias/uncertainty ratios,
then independently validate coverage under modified distortion frequency,
phase and amplitude with additional seeds.

## Per-case parametric-bootstrap bias audit — 24 October 2026

Analyzed the richer 108-row CSV (36 unique cases × three methods) from
MLflow run `d395e37b2161491cb31b44158481fcd3`.

**Known-noise Gaussian bootstrap control:**

| Type | Mean absolute center-1 error | Mean absolute center-2 error | Mean full center-1 interval width | Mean full center-2 width |
| --- | ---: | ---: | ---: | ---: |
| Clean (12) | 0.007 MHz | 0.002 MHz | 0.020 MHz | 0.026 MHz |
| Oscillatory (24) | 0.582 MHz | 0.552 MHz | 0.025 MHz | 0.020 MHz |

The Gaussian noise-only bootstrap intervals on oscillatory spectra are
much narrower than actual center-estimation errors. The two clean
Gaussian misses for center 1 are seed/case 20261224/003_clean_0
(error -0.0127 MHz, full interval width 0.0186 MHz) and
20261225/001_clean_0 (+0.0175 MHz, width 0.0266 MHz).
For oscillatory cases the residual-bootstrap intervals broadened
substantially relative to the Gaussian control, but neither method
achieved joint coverage in the 24 cases.

**Interpretation:** a correct random-noise model around a misspecified
spectral line shape does not capture coherent model bias. Even the clean
case warrants larger independent coverage experiments. Future methods
should explicitly model or detect coherent oscillatory residuals;
calibration must be tested on independent synthetic draws and distinct
distortion regimes. No changes to production quality labels.

## Sinusoidal nuisance-model research milestone — implementation

Added an independent exploratory double-Lorentzian-plus-sine/cosine
fitter and comparison benchmark. The model searches a fixed grid of
candidate nuisance periods (4–9 MHz), reoptimizing the Lorentzian
centers for each candidate. AICc comparison is reported, **without
accounting for the period grid search**. The study evaluates clean
spectra and oscillatory spectra, with independently seeded holdout
parameter/noise draws and shifted oscillation periods/phases. It logs
true maximum resonance-center error, RMSE, model selection and
resonance accuracy to immutable local MLflow artifacts. See
[the experimental protocol](NUISANCE_MODEL_STUDY.md). No benchmark
results have yet been validated, and production QC is unchanged.

## Sinusoidal nuisance benchmark results — 24 October 2026

Two benchmark runs completed, including the 72-case experiment
(12 development and 12 held-out latent draws, each under clean,
low-amplitude and high-amplitude sinusoidal conditions).
MLflow run `f439813c35eb4b71aa41adb4f0191151`.

Mean **maximum absolute two-center error (MHz)**:

| Dataset | Signal | Baseline | Nuisance | AICc-selected |
| --- | --- | ---: | ---: | ---: |
| Development | Clean | 0.00550 | 0.00706 | 0.00676 |
| Development | Low oscillation | 0.25488 | 0.00692 | 0.00692 |
| Development | High oscillation | 0.58305 | 0.00515 | 0.00515 |
| Held-out | Clean | 0.00882 | 0.00810 | 0.00838 |
| Held-out | Low oscillation | 0.27253 | 0.04624 | 0.04624 |
| Held-out | High oscillation | 0.57706 | 0.09603 | 0.09603 |

Thus held-out average center error fell by approximately **83.0%**
(low) and **83.4%** (high). On development sinusoidal cases the
improvements were approximately 97.3% and 99.1%. The shifted held-out
generator uses periods/phases different from development, but still
simulates the same sinusoid family used by the nuisance fitter.

**Unnecessary complexity:** AICc selected nuisance on 7/12 clean
development spectra and 6/12 clean held-out spectra. AICc computation
does not correct for searching six fixed candidate periods and is not
sufficient evidence to deploy model selection. No production QC
changes. Next inspect per-case periods, center errors and selection
flags; evaluate non-sinusoidal structured residuals, period-grid shifts,
clean false-selection control and uncertainty calibration for the
nuisance model before any promotion.

## Nuisance-model per-case audit — 72-case held-out study

Audited the uploaded `nuisance_comparison.csv` for local MLflow run
`f439813c35eb4b71aa41adb4f0191151`. Across **48 oscillatory cases**,
the sinusoidal nuisance fitter reduced the maximum absolute two-center
error in **every case**. The original two-Lorentzian model was inaccurate
(>0.5 MHz) in 15/48 cases; the nuisance model was within the illustrative
0.5 MHz tolerance in 48/48. Neither classification is instrument validation.

Across all 24 clean examples, AICc selected the nuisance model 13
times (7/12 development; 6/12 held-out). On clean data the fitted
nuisance amplitude ranged from approximately 0.000061 to 0.000155
normalized contrast units; fitted oscillatory-case amplitudes started
around 0.00531. The clean/oscillatory amplitude gap is a property of
this synthetic generator, not a justified production threshold.

Held-out oscillatory cases by selected period:
- 5 MHz (8 cases): mean center error 0.0630 MHz;
- 7 MHz (8 cases): mean center error 0.0487 MHz;
- 9 MHz (8 cases): mean center error 0.1018 MHz.

Worst held-out nuisance errors: `heldout_008_oscillation_high`
0.1947 MHz (baseline 1.1828); `heldout_002_oscillation_high`
0.1809 MHz (baseline 0.2203); and
`heldout_011_oscillation_high` 0.1328 MHz (baseline 0.2910).
All selected a 9 MHz candidate, while the relevant held-out
generator period is 8.6 MHz, suggesting that coarse period search
may leave residual center bias.

**Next research controls:** refine period continuously after grid
initialization; compare against the unchanged six-grid-period method;
test clean false-selection rates with a selection method that accounts
for period searching; and evaluate unrelated distortions before
considering any production integration.

## Continuous-period refinement and selection research — implementation

Added research-only joint continuous optimization of the sinusoidal
period (initialized from the existing candidate grid), a deliberately
conservative extra-AICc-penalty selection experiment, new per-case
development/held-out comparisons, and tests. See
[period refinement protocol](PERIOD_REFINEMENT.md). The extra
penalty of 8 is exploratory rather than a calibrated multiple-period
search correction. No benchmark outcome is claimed until local or CI
verification and held-out execution; production fitting/QC unchanged.

## Phase 2 — Generalization beyond sinusoidal interference

After merging PR #2 into `main`, began a separate research branch
`feat/odmr-robustness`. Added reproducible, paired synthetic challenges:
clean, single-sine, two-tone, frequency chirp, harmonics and curved
baseline, each scored under an independent shifted regime. The
benchmark compares true center-estimation error of baseline,
fixed-grid nuisance, continuous nuisance and conservatively selected
fits. It writes new MLflow artifacts and has reproducibility tests.
See [the Phase 2 study](ROBUSTNESS_STUDY.md).

**Evidence status:** implementation committed; CI and experiment results
not yet verified. Do not conclude generalization or alter production
QC based solely on this implementation.

## Phase 2 shifted non-sinusoidal benchmark — 24 October 2026

Run `ed1b659f8ca643aca51236ccfe5b6601` (local MLflow),
seeded development 20261024 vs shifted 20271124, 12 independent
latent draws × six distortion families per split (144 total).
Illustrative parameter-accuracy tolerance: 0.5 MHz.

Shifted-set mean maximum two-center errors in MHz, **baseline →
penalty-selected**: clean 0.009684→0.009733; single sine
0.816143→0.012849; two-tone 1.157723→1.043113; chirp
1.115554→1.233618; harmonics 0.491877→0.110712; curved
baseline 0.013236→0.015550.

Nuisance was selected on shifted cases 1/12 clean, 12/12 single
sine, 12/12 two-tone, 12/12 chirp, 12/12 harmonics and 6/12
curved baseline. Nine selected shifted fits exceeded the illustrative
0.5 MHz error tolerance: **three two-tone and six chirp**; no
selected failures for the other families.

The strong positive single-sine and harmonic results coexist with
weak two-tone results and a negative chirp result (mean error increased
10.6%). This benchmark explicitly refutes unrestricted
generalization from the original sinusoidal research successes.
No production model or QC policy was changed.

**Next:** inspect per-case errors in `robustness_cases.csv`,
compare baseline and selected false/true acceptances on each shifted
family, and consider a separate abstention/model-mismatch warning
rather than automatically trusting an AICc-preferred nuisance model.
Do not tune against the same held-out split and then reuse it as
untouched evidence.

## Phase 2 per-case reliability audit — 24 October 2026

Inspected uploaded 144-case `robustness_cases.csv` plus study summary.

Exactly **nine shifted cases** exceeded the illustrative 0.5 MHz
two-center error tolerance after penalty-based selection: three
two-tone and six chirp cases. All selected the refined nuisance fit.

| Case | Baseline max error MHz | Selected max error MHz | Refined RMSE improvement |
| --- | ---: | ---: | ---: |
| shift_000_two_tone | 0.973 | 0.774 | 27.0% |
| shift_002_two_tone | 8.605 | 8.938 | 19.4% |
| shift_005_two_tone | 0.790 | 0.673 | 30.4% |
| shift_001_chirp | 0.481 | 0.680 | 6.9% |
| shift_003_chirp | 0.375 | 0.822 | 10.4% |
| shift_005_chirp | 0.552 | 0.573 | 11.0% |
| shift_006_chirp | 0.590 | 0.735 | 10.3% |
| shift_007_chirp | 9.685 | 9.567 | 11.0% |
| shift_008_chirp | 0.391 | 0.602 | 7.7% |

**Three newly inaccurate chirp decisions** (`shift_001_chirp`,
`shift_003_chirp`, `shift_008_chirp`) had baseline errors below
0.5 MHz but selected-model errors above 0.5 MHz. All nine cases
reduced residual RMSE while some center estimates worsened.

Mean shifted RMSE reductions: single sine 86.7%, harmonics 57.9%,
two-tone 29.8%, chirp 8.8%, clean 0.8%, curved baseline 1.7%.
Substantial RMSE improvements are therefore not proof of center
accuracy, particularly for two-tone distortions.

**Diagnostic gap:** the existing benchmark CSV exports absolute
center-error magnitudes, fitted periods and RMSE but does not export
individual baseline/refined centers, signed errors, or spectral residual
features. Therefore it does not establish actual center displacement,
peak identity or a valid new alert threshold.

**Next:** add center coordinates, signed errors, residual correlation
and frequency-dependent residual metrics to new immutable run
artifacts. Develop any model-mismatch warning on a distinct development
cohort and validate on genuinely untouched seeds/regimes. Production
FIT_OK/REVIEW_REQUIRED/FIT_FAILED rules remain unchanged.

## MVP packaging — 24 October 2026

The first MVP integration adds `measurement_report.json` and `measurement_report.html` to the existing `scripts.diagnose_odmr` analysis run, alongside CSV and fit plots. Statuses remain provisional fit diagnostics, not calibrated measurement or current-map quality. The interface still uses the existing CLI; a streamlined installed command, reference manifest, polished demonstration and release validation remain outstanding. CI not yet verified for these commits.
