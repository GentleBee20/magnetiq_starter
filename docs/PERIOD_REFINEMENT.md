## Continuous period refinement and merge decision

**Status: experimental; not integrated into operational diagnostics.**

The existing fixed-period nuisance fitter tests a 4–9 MHz period grid.
The additional research routine starts from the best grid candidate
and fits the period continuously, jointly with Lorentzian and nuisance
parameters. The benchmark reports the original double-Lorentzian,
fixed-grid nuisance, refined nuisance, and penalty-selected center
errors on independent development and shifted held-out synthetic data.

A deliberately conservative selection heuristic requires the nuisance
AICc advantage to exceed an additional configurable penalty of 8.
That number is **not a statistical correction** for the frequency search
and must be validated against clean false selections and center accuracy.
The period-refinement AICc counts 11 parameters (including period);
the fixed-grid AICc counts 10 and omits the discrete search cost.

Run:

```powershell
python -m scripts.benchmark_period_refinement --repeats 6
```

Output: `reports/odmr/benchmarks/refined_period.csv`; it refuses to
overwrite existing outputs. Rerun with `--output` set to a new path.

**Merge criterion:** keep production QC unchanged, obtain a green CI
run (Ruff, mypy, pytest), review per-case clean and held-out comparisons,
and demonstrate the research tools are isolated and documented.
Merging a research-only feature into main is reasonable after these
requirements; promotion of the nuisance model into production demands
additional non-sinusoidal tests, real data and independent calibration.
