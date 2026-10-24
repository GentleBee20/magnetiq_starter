# Held-out synthetic adequacy-policy validation

## Purpose

Test whether residual-based severity rules predict unacceptable resonance-center
error without selecting thresholds on the evaluation cases. This does **not**
validate quantum-sensing hardware, nor does it change production QC.

## Run

```powershell
python scripts\validate_adequacy_policy.py --train-seed 20261024 --test-seed 20261124 --repeats 12 --tolerance-mhz 0.5
```

The script creates 192 train and 192 held-out rows, chooses from a
**predeclared finite grid** of relative RMSE and absolute lag-1 thresholds
using **training data only**, with a maximum training false-failure rate
of 5%, then evaluates existing, previous-candidate and tuned policies on
the unseen held-out seed. It never overwrites reports, and logs all policies
and per-case CSVs into the existing local MLflow experiment.

Important: `REVIEW_REQUIRED` is an **abstention**, not a false acceptance.
The selection aims to catch inaccurate centers among the reviewed spectra,
not reinterpret previously accepted results. Report all of failure recall,
false-failure rate, false-acceptance rate, and review rate.

## Caveats

- Both splits use the **same generator**, distortions, fixed sweep and fixed
  noise amplitude. A new seed tests parameter/noise draws, not new physics.
- Identical zero-distortion signals repeat across categories within a draw;
  rows are not independent observations. Effective sample size is smaller.
- The center-error tolerance 0.5 MHz is illustrative, not a physical
  requirement. No expert-labeled real-spectra test set exists yet.
- Comparing multiple thresholds on train still entails selection bias; only
  report held-out results as exploratory, not a guarantee.
- Future work: different distortion *families*, shift in noise/SNR,
  independent held-out seeds, grouped bootstrap, realistic amplitude and
  linewidth regimes, formal review/abstention cost.

See [project story](PROJECT_STORY.md) for the evidence ledger.
