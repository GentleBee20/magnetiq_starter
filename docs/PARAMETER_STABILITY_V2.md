# Parameter stability v2: objective-aware restarts

The research pipeline now records, for each successful optimizer restart:
two fitted centers, residual sum of squares (RSS), RSS relative to the
original selected double-Lorentzian fit, and whether any model parameter
approaches its optimization bound. A restart is **near-optimal** when its
RSS is at most 1.01 times the baseline RSS (configurable). The summary
reports both full-restart and near-optimal center ranges.

The bootstrap also now exports two separate empirical percentile intervals,
one for each sorted resonance center. They are **not** calibrated confidence
intervals under structured residual mismatch or model misspecification.

Run a new non-overwriting MLflow experiment:

```powershell
python -m scripts.benchmark_stability --seed 20261124 --repeats 3 --bootstrap 20 --starts 8 --near-optimal-rss-ratio 1.01
```

Inspect `center_stability.csv` and `restart_details.csv` in the new run
folder. The former exposes interval endpoints and filtered center ranges;
the latter exposes which solutions have poor objective scores or touch bounds.

**Interpretation:** near-optimal agreement is only evidence about the
optimization landscape. It cannot rule out a consistently biased line-shape
model. Our next experiment must test empirical bootstrap interval *coverage*
on many synthetic truth-known spectra, including shifted noise and
oscillation regimes and grouped held-out draws. Production QC is unchanged.
