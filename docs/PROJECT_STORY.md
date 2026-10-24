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
