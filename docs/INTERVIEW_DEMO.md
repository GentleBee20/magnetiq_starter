# MagnetIQ — five-minute technical interview walkthrough

**Audience:** Data scientists and measurement/software engineers.  
**Goal:** Demonstrate the released v0.1.0 project without claiming validated sensor accuracy.

## 0:00–0:45 — Explain the problem

> An optimizer can converge to a plausible ODMR fit while leaving structured
> residuals. I built MagnetIQ to make such evidence visible and to recommend
> investigation instead of equating convergence with trustworthy physics.

Show the GitHub release and the
[technical case study](PORTFOLIO_CASE_STUDY.md).

## 0:45–1:30 — Show reproducibility

From a repository checkout with the independently downloaded Zenodo archive:

```powershell
magnetiq analyze "data\raw\Dataset_10.5281zenodo.14697917.zip" --run-name "interview-demo"
```

Open the resulting `measurement_report.html`. Explain the unique run
directory, manifest, structured JSON/CSV outputs and MLflow tracking.

**Do not run the full dataset live if execution time is uncertain.**
A previously generated local report is sufficient to discuss the results;
use `--limit 6` for a shorter live demonstration.

## 1:30–3:20 — Three illustrative spectra

1. **Pilot row 1, Hole2 NV1:** Selected double-Lorentzian; normalized
   RMSE 0.0607; lag-1 correlation 0.246; maximum local RMSE ratio 1.37.
   No triggered warnings, provisional `FIT_OK`.
2. **Pilot row 2, Hole2 NV3:** Normalized RMSE 0.0588 is slightly
   *smaller* than row 1, but lag-1 residual correlation 0.712 and local
   RMSE ratio 3.31 trigger two review codes. Open its plot and discuss
   why local residual behavior matters.
3. **Pilot row 45, Hole4 NV17:** Baseline selected; despite normalized
   RMSE 0.0214, no resonance is selected. The `REVIEW_REQUIRED` status
   prevents declaring successful resonance extraction from a low error alone.

These row indices describe the 105-spectrum pilot; use the **source paths**
in the case-study table if another run orders measurements differently.

## 3:20–4:20 — Scientific maturity

Explain that an experimental sinusoidal nuisance model sometimes fits
synthetic sinusoidal corruption well but does not reliably generalize to
chirps, two-tone interference and other disturbances. Fitting RMSE can
improve while resonance-center accuracy worsens. Keep those models in
a research branch/benchmark rather than automatically changing
operational fit-quality thresholds.

Point to [ROBUSTNESS_STUDY.md](ROBUSTNESS_STUDY.md).

## 4:20–5:00 — Close with constraints and next step

> The release evaluates spectral-fit evidence; it does not calibrate a
> quantum sensor, reconstruct a field map or identify a semiconductor
> fault. The next credible scientific milestone is an independently
> labelled reference benchmark and quantified parameter uncertainty.

Invite questions about AICc, identifiability, residual autocorrelation,
local-noise normalization, the threshold policy or MLflow provenance.

## Questions to prepare for

**Why do 69 of 105 require review?**
The thresholds are provisional and intentionally diagnostic. With no
expert ground truth, the count alone says nothing about accuracy.

**Why no FIT_FAILED cases?**
The current operational failure behavior is narrow; a converged but
physically poor fit can still be `REVIEW_REQUIRED`. Do not claim that
all 105 models are acceptable.

**Why AICc?**
It compares candidate fits while accounting for their complexity,
but model preference and model adequacy are separate questions.

**What did the negative experiments teach you?**
Lower residual error is not equivalent to better physical parameter
estimates. I preserved negative evidence and did not silently deploy
a nuisance model beyond the tested family.

**Could this identify chip defects?**
Not from these spectra or the present labels. That would require
calibrated sensing, spatial data and validated downstream physics.
