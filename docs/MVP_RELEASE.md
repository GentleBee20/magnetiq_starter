# MagnetIQ v0.1.0 — MVP release candidate

## Product scope

MagnetIQ is a command-line tool for explainable **ODMR spectral-fit quality**
evaluation on a public experimental data archive. It fits candidate Lorentzian
models, assigns **provisional** fit-quality statuses with reason codes and
investigation suggestions, and exports inspectable reports.

It **does not** validate sensor calibration, reconstruct magnetic fields or
3D current maps, diagnose semiconductor defects, or establish customer-ready
measurement quality. Experimental sinusoidal nuisance models, bootstrap
research, and synthetic robustness benchmarks remain separate from the
routine verdict workflow.

## Reproduce a full evaluation

Install with Python 3.10–3.12 from the repository root:

```powershell
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
python -m pytest -q
magnetiq analyze "data\raw\Dataset_10.5281zenodo.14697917.zip" --run-name "v0.1.0-demo"
```

Download the public Zenodo archive separately as described in README; its
third-party contents are not committed to the repository.

Every run creates a unique output directory. Inspect:

- `measurement_report.html`: human-readable provisional verdicts and investigative guidance
- `measurement_report.json`: structured model diagnostics and artifact explanations
- `fit_diagnostics.csv`: per-spectrum numerical diagnostics and warning codes
- `plots/` and `summary.png`: measured signals, fits and residuals
- `manifest.json`: provenance; MLflow tracks run metadata and artifacts

## Evidence available at release-candidate stage

A locally executed full-dataset pilot reported **105 spectra processed**:
36 `FIT_OK`, 69 `REVIEW_REQUIRED`, 0 `FIT_FAILED`. These are the
outputs of heuristic fit diagnostics, **not accuracy labels**.

Pilot MLflow ID: `f1fdb16c8c324ac7952fdbe8bb6c2585`.
Its ignored local data and report artifacts are not automatically included
in the GitHub repository or release.

The feature branch passed its quality matrix at commit `a9547090`.
New commits, including this document, must pass CI again before merge.

## Release gate

- [x] Repeatable public-data analysis executed on all 105 spectra
- [x] Provisional verdicts, warnings, plots and reports implemented
- [x] Artifact catalogue suggests next investigations, not causal diagnoses
- [x] Installed `magnetiq analyze` CLI tested locally
- [x] GitHub quality CI passed at `a9547090`
- [ ] Verify the final candidate's CI after documentation changes
- [ ] Inspect final HTML report readability and links on representative cases
- [ ] Confirm report JSON parses and includes 105 records for the final run
- [ ] Merge the release candidate into protected `main`
- [ ] Tag `v0.1.0` only from the merged, passing `main` commit

## Inspecting the released analysis

1. Analyze the independently downloaded public ODMR dataset.
2. Open the HTML report and inspect contrasting `FIT_OK` and `REVIEW_REQUIRED` cases using linked diagnostic plots.
3. Review warning evidence and the relevant follow-up checks.
4. Examine the synthetic robustness experiments, including cases where smaller fitting error does not improve resonance-center accuracy.
5. Inspect MLflow provenance, the manifest and the evidence ledger.

See `docs/PROJECT_STORY.md` and `docs/ROBUSTNESS_STUDY.md` for scientific limitations and negative results.
