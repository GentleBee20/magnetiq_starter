# Full Zenodo scientific archive inspection

The [Zenodo record](https://doi.org/10.5281/zenodo.14697917)
describes four data families: **ODMR**, **Coherence** (Ramsey and spin echo
measurements and fits), **Profile** (as-grown sample surface), and **Scan**
(images used to identify single NV centers).

The existing, locally inspected manifest verifies **105 text ODMR spectra**
within 152 archive files: 129 TXT, 20 PNG, 2 PDF and 1 nested ZIP.
This alone does **not** establish the actual contents of the non-ODMR files,
their physical units or whether independent ground-truth labels exist.

## Read-only local inspection

Run from the repository root with the original archive present:

```powershell
python -m scripts.inventory_full_dataset "data\raw\Dataset_10.5281zenodo.14697917.zip"
```

This generates ignored files:

- `reports/dataset_inventory/full_inventory.json`: archive SHA-256, groups,
  file sizes, text headers, sample column counts, unit tokens, PNG dimensions,
  nested ZIP contents and inspection errors
- `reports/dataset_inventory/full_inventory.md`: human-readable file inventory

It **does not extract or modify the archive**, and only reads up to 64 KiB of
each text/image file. PDF metadata is limited to file signatures; documents
require separate review. Numeric previews are not scientific verification.

## Research decision after inspection

1. Determine whether Ramsey / spin-echo **raw time series** and fitted
   outputs support decay-model goodness-of-fit and repeatability checks.
2. Determine whether scan/profile images have quantitative spatial scales,
   axes and accessible intensity arrays for image-quality diagnostics.
3. Identify potential paired repeat measurements using actual methods,
   rather than treating filenames as independently validated metadata.
4. Document which expected references, independent truth, calibration
   parameters or spatial field maps are absent.

Do not infer magnetic-field or current-density reconstruction from NV
scan images without the necessary physically calibrated data.
