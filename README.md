# MagnetIQ — quantum measurement quality MVP

Initial scope: inventory real NV-center experimental data, identify usable ODMR spectra, then implement transparent fitting, uncertainty estimates, artifact checks, and explainable measurement verdicts.

Data: Zenodo https://doi.org/10.5281/zenodo.14697917 (download separately; not included in repo).

## Quick start (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts\inspect_archive.py data\raw\Dataset_10.5281zenodo.14697917.zip
python -m pytest -q
```

The inspector does *not* extract or load large arrays; it inventories the ZIP safely and writes reports/archive_inventory.json and reports/archive_inventory.csv. Return the terminal summary and inventory to guide data parsing.

Do not commit third-party datasets to GitHub. The datasets have their own usage conditions; retain publication citation and provenance.
