# MagnetIQ — ODMR spectral-fit reliability: technical case study

**Released software:** [MagnetIQ v0.1.0](https://github.com/GentleBee20/magnetiq_starter/releases/tag/v0.1.0)  
**Domain:** NV-center optically detected magnetic resonance (ODMR) spectroscopy  
**Stack:** Python, NumPy/SciPy, MLflow, pytest, Ruff, mypy, GitHub Actions  
**Data:** [public experimental ODMR archive](https://doi.org/10.5281/zenodo.14697917)

## The engineering problem

In nonlinear spectral fitting, convergence and a visually plausible fit do not
establish that the selected model adequately explains the measurement.
Correlated residuals, localized mismatches or parameter constraints can make
fitted resonance parameters questionable even when the global error is small.

**Question:** How can an analyst automatically identify which ODMR spectral fits
deserve closer inspection, and make that recommendation traceable?

This is *spectral-fit* quality analysis, not calibration, current-density
reconstruction, 3D magnetic-field mapping or semiconductor defect identification.

## Solution and architecture

```text
Public ODMR ZIP
  -> spectrum reading and validation
  -> baseline / one-Lorentzian / two-Lorentzian candidate fits
  -> AICc-based candidate selection
  -> global, structured and resonance-local residual diagnostics
  -> provisional fit-quality status + evidence-coded warnings
  -> HTML / JSON / CSV / diagnostic plots
  -> immutable run directory + MLflow / manifest
```

The `magnetiq analyze` command orchestrates a reproducible batch evaluation.
The report intentionally separates **observations**, **heuristic interpretation**
and **suggested next checks**.

## Results from the public dataset

A complete run processed **105 experimental spectra**:

| Provisional fit status | Count |
| --- | ---: |
| `FIT_OK` | 36 |
| `REVIEW_REQUIRED` | 69 |
| `FIT_FAILED` | 0 |

The proportions are **not** model accuracy, device quality, the prevalence of
bad hardware, or a performance improvement metric. There are no independently
adjudicated quality labels for these measurements.

## Three real, traceable case examples

The row numbers below refer to the released report's deterministic row order
in the provided full-dataset pilot. Plot filenames are relative to its run
directory; re-runs may use different output directories.

| Pilot row | Selected fit | Evidence | Provisional status |
| --- | --- | --- | --- |
| 1 — Hole2, 2023-05-23 03:01, NV1 | Double Lorentzian | Normalized RMSE **0.0607**, lag-1 residual correlation **0.246**, maximum resonance-local RMSE ratio **1.37** | `FIT_OK` |
| 2 — Hole2, 2023-05-23 17:17, NV3 | Double Lorentzian | Normalized RMSE **0.0588**, lag-1 correlation **0.712**, maximum resonance-local RMSE ratio **3.31** | `REVIEW_REQUIRED` |
| 45 — Hole4, 2023-07-30 00:39, NV17 | Baseline | No resonance selected; normalized RMSE **0.0214** | `REVIEW_REQUIRED` |

**Example A — a fit that passes the current checks.** Row 1 gives an
illustrative `FIT_OK` verdict: the selected double-Lorentzian fit has no
triggered provisional warnings. This does not certify that its centers are
physically correct.

**Example B — similar global fit error, different residual evidence.** Row 2
has slightly *lower* normalized RMSE than row 1, yet residual correlation
exceeds the current review limit of 0.7 and local RMSE ratio exceeds the
current limit of 2. The report flags `structured_residuals` and
`resonance_local_residual_excess`; inspecting residual shapes or alternative
line shapes is justified. **This is the central demonstration: optimizing
a single aggregate error score can miss localized model inadequacy.**

**Example C — no supported resonance despite small residuals.** Row 45
selects a baseline model with no fitted resonance, and receives
`no_resonance_selected`. Its low normalized RMSE alone must not be
misrepresented as successful resonance estimation. The correct next checks
concern usable spectral contrast, acquisition range and candidate fits.

To inspect the associated plot in a local run, open
`measurement_report.html` and select the row's **View fit plot** link;
those plotted files and raw spectra are not packaged into the Git tag.

## Reproducible demonstration

```powershell
python -m pip install -e ".[dev]"
magnetiq analyze "data\raw\Dataset_10.5281zenodo.14697917.zip" --run-name "portfolio-demo"
```

Find the newly created directory under
`reports/odmr/experiments/runs/`. Open `measurement_report.html`,
then examine `measurement_report.json`, `fit_diagnostics.csv`,
`manifest.json`, `summary.png` and `plots/`.

```powershell
ruff check .
ruff format --check .
mypy
python -m pytest -q
```

## Engineering decisions and trade-offs

- **Transparent candidates over a black-box classifier:** AICc and
  bounded Lorentzian fits are inspectable, but selection is not proof of
  physical adequacy.
- **Multiple residual perspectives:** Global normalized RMSE, lag-1
  correlation and local resonance metrics highlight different shortcomings.
- **Abstention via review:** `REVIEW_REQUIRED` marks uncertainty and
  investigation needs; it does not invent a hardware-failure diagnosis.
- **Research separated from production:** Synthetic stress experiments
  tested oscillatory nuisance models and uncovered poor transfer to
  chirps/two-tone interference. Lower residual error sometimes failed to
  improve resonance-center estimates, so those research fits were *not*
  silently promoted to the operational workflow.
- **Traceability:** Run-specific outputs, provenance manifests, source
  identifiers and MLflow make comparisons reproducible rather than
  overwriting a previous result.

## Limitations and next scientific steps

The heuristic review thresholds have not been validated against expert
ground truth; there is no established sensitivity/specificity for real
measurement problems. A future study should acquire independent reference
measurements, quantify center/linewidth uncertainty, test held-out
distortion regimes and set explicitly justified acceptance tolerances.

**Engineering conclusion:** The pipeline provides reproducible, inspectable
fit-quality evidence while keeping numerical model adequacy distinct from
validated physical measurement accuracy.

See [the experiment ledger](PROJECT_STORY.md),
[robustness limitations](ROBUSTNESS_STUDY.md) and
[release scope](MVP_RELEASE.md).
