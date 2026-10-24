# MagnetIQ — quantum measurement quality MVP

A reproducible, engineering-focused pipeline for real NV-center experimental data.
The goal is explainable measurement quality assessment; reconstructed 3D current maps
are **not** validated by the first spectroscopy dataset.

## Dataset

[NV-center experiment, Zenodo DOI 10.5281/zenodo.14697917](https://doi.org/10.5281/zenodo.14697917).
Download separately into `data/raw/`. Third-party data is excluded from Git.

## Development setup (PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
python -m pytest -q
```

## Inspect experimental dataset

```powershell
python scripts\inspect_archive.py "data\raw\Dataset_10.5281zenodo.14697917.zip"
```

Manifests are generated in `reports/` (excluded from version control).
The inspection is read-only and does not extract or load measurement arrays.

## Engineering conventions

- Reusable functions live under `src/magnetiq/`; `scripts/` are thin CLI entry points.
- Library code does not configure logging. CLI entry points call `configure_logging`.
- Use standard `logging` with lazy %-style formatting instead of print.
- Keep scientific units, calibration assumptions and provenance explicit.
- Add pytest cases for both success and failure behavior.
- Require Ruff, mypy and pytest checks before merge.
- Develop isolated features on branches and merge into `main` by pull request.

## First exploratory ODMR analysis

```powershell
python scripts\analyze_odmr.py "data\raw\Dataset_10.5281zenodo.14697917.zip" --plot-count 6
```

Writes `reports/odmr/spectrum_summary.csv` and
`reports/odmr/representative_spectra.png`. These are **model-free descriptive
statistics only**; minimum contrast is not proof of a physical resonance,
and median adjacent differences are not calibrated instrument noise.
