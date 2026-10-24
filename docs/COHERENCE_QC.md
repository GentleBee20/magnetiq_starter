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

## Initial real-data review (24 files)

The first run produced 24 rows: 12 Ramsey and 12 spin-echo measurements.
The exploratory report flagged **5 Ramsey files** and **0 spin-echo files**:

- Four Ramsey files: `structured_residuals_exploratory`.
- One Ramsey file: `localized_residual_excess_exploratory`.

Examples include No Hole/NV2 (`2022-10-01 21:21`) and Hole/NV6
(`2022-11-06 22:19`), where pronounced residual drift or structure
is visible. For Hole/NV2 (`2022-10-28 08:55`), localized residual
error is flagged. Other unflagged plots can *also* exhibit nonzero
residual bias or systematic excursions, meaning these exploratory
flags are **not comprehensive quality labels**.

Across the supplied figures, Ramsey signals have markedly differing
absolute magnitudes (including ~1 and values in the tens/hundreds of
thousands), while echo traces are commonly around 0.01–0.06.
Do not compare their unnormalized errors or interpret `Envelope`
as a statistical confidence interval.

The displayed orange author-fit curves sometimes oscillate strongly
while the measured blue data show residual drift. It is not possible
to distinguish acquisition artifacts, fit misspecification, differing
normalization or deliberate model choices from plots alone.
Investigate the authors' model definitions and acquisition methods
before attributing causes.

**Priority for follow-up:** add signed residual bias and an early/late
drift diagnostic, then test them on synthetic reference cases before
assigning interpretation thresholds. Also examine the presence of
strongly nonuniform tau sampling before using lag-based metrics.


## Residual-bias research metrics (experimental)

The CSV now also records the following **descriptive** quantities for
each measurement, without creating additional quality flags:

- `mean_residual`: mean of `Data - Fit` in the file's reported signal units.
- `signed_bias_over_rmse`: signed mean residual divided by that file's
  RMSE, bounded between -1 and +1 when RMSE is nonzero; a signed indication
  of persistent offset rather than goodness-of-fit.
- `early_late_bias_difference_over_rmse`: difference in mean residual
  between the latter and earlier halves of the sampled time sequence,
  divided by RMSE. It indicates changing average residual, **not** a
  confirmed physical drift mechanism. Halves are split by sample count,
  not equal duration.
- `sampling_step_max_min_ratio`: largest over smallest successive
  `tau` increment. Values above 1 indicate uneven temporal sampling;
  this matters when interpreting sample-index lag correlations.

The ratios use each file's own RMSE, so they are invariant under
multiplication of all signal values by the same nonzero positive scale.
If residual RMSE is zero, bias ratios are defined as zero by convention.

These metrics are research leads. No new thresholds, accepted/rejected
labels, or sensor-failure diagnoses are introduced.


## Results from the 24-file residual-bias CSV

The submitted real-data run confirms 12 Ramsey and 12 spin-echo
measurements. All 24 have a maximum/minimum sampling-step ratio of 1.0.

For descriptive investigation only (not a new acceptance threshold),
8/12 Ramsey files have `abs(signed_bias_over_rmse) > 0.5`,
versus 0/12 spin-echo files. All six Hole-region Ramsey files
have negative signed bias of magnitude about 0.55–0.85 RMSE; two
No-Hole Ramsey files also show negative bias. Multiple such files
have no existing quality warning, confirming that existing exploratory
flags do not fully describe persistent residual offset.

Using `abs(early_late_bias_difference_over_rmse) > 0.7`
as another *descriptive selection criterion*, 8/12 Ramsey files
and 4/12 spin-echo files qualify. These differences can arise from
fitting conventions, oscillatory residuals or model mismatch;
they are **not proof of instrument drift**.

The spin-echo fitted residuals have mean values extremely close to
zero relative to RMSE, while Ramsey measurements are heterogeneous
in their mean offsets. The provided fit-generation methods and
baseline conventions must be investigated before assigning a cause
or introducing operational warning thresholds.
