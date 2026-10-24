# Exploratory coherence-fit quality analysis

MagnetIQ can now inspect the 24 author-provided Ramsey and spin-echo files
from the Zenodo dataset, separately from the ODMR pipeline.

## Run

```powershell
python -m scripts.analyze_coherence "data\raw\Dataset_10.5281zenodo.14697917.zip"
```

Open `reports/coherence/coherence_report.html`. The pipeline writes
`coherence_diagnostics.csv` and individual plots in `plots/` with
Data, author-provided Fit, Envelope, and Data-minus-Fit residuals.

## Interpretation

- Read-only processing: original archive is never extracted or changed.
- Numerical columns are `tau [ns],Data,Fit,Envelope`; signal units
  are not established and signal scale differs dramatically among files.
- Relative RMSE is normalized by the measured `Data` range **within
  each spectrum**. It is undefined for constant signals. This is a
  descriptive, scale-aware metric, not an uncertainty-calibrated error.
- Lag-1 residual correlation and maximum five-window residual-RMSE ratio
  expose possible residual structure and nonuniform fit quality.
- Exploratory flags use unvalidated cutoffs (|lag-1| > 0.6, local ratio > 1.8).
  They are **not acceptance criteria** and do not diagnose hardware faults.
- `Fit` and `Envelope` are author-supplied curves, **not independent
  physical ground truth**; the envelope convention remains unverified.
- Do not compare raw RMSE between Ramsey and spin-echo, or interpret
  Hole/No Hole as verified fit-quality labels.
- The present report evaluates already fitted signals; it does not
  refit decay models, estimate T2/T2*, or validate uncertainty coverage.

Next: inspect complete 24-file output, verify the envelope definition against
the authors' methods, and then design held-out synthetic tests.
