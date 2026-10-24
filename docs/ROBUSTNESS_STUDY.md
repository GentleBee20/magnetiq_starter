# Phase 2 — Non-sinusoidal robustness study

**Research-only.** The merged ODMR fitter and operational fit-QC statuses
are unchanged.

We previously observed strong improvements from a Lorentzian plus sinusoidal
nuisance model on data generated with a related sinusoid. This experiment
asks whether that improvement survives more diverse interference.

Test cases per independent latent parameter draw:
- Clean (noise-only reference).
- Single sinusoid (in-family positive control).
- Two-tone oscillatory interference.
- Frequency-chirped interference.
- Sinusoid with second harmonic.
- Curved baseline (out-of-family negative control).

The shifted split uses a different seed, altered nominal period,
stronger interference and noise, and stronger chirp. Do not tune on
this split and then describe it as untouched held-out evidence.

Compare baseline double-Lorentzian, fixed-grid nuisance,
continuous-period nuisance, and penalty-selected model. Report **true
maximum center error**, illustrative 0.5 MHz tolerance, selection
rates on clean data, and runtime/fit failures. Lower RMSE alone is
not evidence of better center estimates.

Run from repository root:

```powershell
python -m scripts.benchmark_robustness --repeats 3
```

Then extend to `--repeats 12`. Each run produces a new MLflow record
and immutable `robustness_cases.csv` and `summary.json`. A
larger suite, independent regimes, and external measurements would
be needed for generalizable validity.

**Merge criterion for this new branch:** green CI on Python
3.10/3.11/3.12, verified execution, and documented negative as
well as positive outcomes. Do not change production QC based on
these synthetic findings.
