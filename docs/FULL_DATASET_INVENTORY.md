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


## Findings from local archive manifest (2026-10-24)

The user-generated inventory identifies **154 listed entries including nested ZIP
contents**. Group totals are 108 ODMR, 24 coherence, 14 scans, and 8 profiles.
The groups count archive objects, **not** independent measurements. File formats
include 131 TXT, 20 PNG, 2 PDF and one nested ZIP.

### ODMR

- 105 distinct top-level spectra had already been processed by MagnetIQ.
- The three extra ODMR entries in the inventory are one nested spectrum,
  its `__MACOSX/._...` metadata file (contains NUL bytes), and the nested ZIP
  itself. This is not evidence of three new independent ODMR measurements.
- A top-level `CRASH_DUMP_...` file warrants its own quality investigation;
  its name alone does not establish whether it is defective.
- Repeated NV identifiers in filenames are potential repeatability candidates,
  but require group/settings verification first.

### Quantum coherence: 24 numerical time series

- 12 Ramsey measurements and 12 spin-echo measurements: six of each in
  `Hole Region` and six of each in `No Hole Region`.
- The text header is consistently `tau [ns],Data,Fit,Envelope`.
- `tau` is time in nanoseconds; `Data` and `Fit` are
  numerical values and `Envelope` is separately included.
  Numerical scale **varies by file**: some Ramsey data begin around
  5,966, 130,029 or 0.999, while spin-echo values begin around 0.02–0.07.
  Do not aggregate raw RMSE across incompatible scale conventions.
- Ramsey and spin echo for each identified NV form natural within-sample
  pairs, subject to provenance checks. They are *different experiments*,
  not duplicate measurements.
- First research objective: reproduce published fit residuals and compare
  normalized residual metrics, lag correlation, coverage of plotted
  envelopes, and stability of refit parameters **without** treating the
  provided fitted values as ground-truth physical parameters.
- The exact `Envelope` convention and fitting formula remain unverified.

### Scan images: 14 PNGs

- All observed files are PNG figure exports, ranging approximately from
  3,490 × 2,922 to 8,003 × 5,758 pixels.
- The inventory provides **no raw 2D instrument intensity arrays**, pixel
  calibration, physical coordinate grid, or magnetic-field values.
- Visually inspect representative images, axis labels and plotting metadata
  before deciding whether any pixel-based processing is scientific.
  Image-quality screening of figure exports is feasible but much weaker
  evidence than instrument-level analysis.

### Surface-profile files: 8 figures

- Six PNGs and two PDFs, including `Pre-cleaning` profile exports.
- No independent numerical height profiles, calibrated axes or paired
  reference maps have been established by this inventory.
- Treat figure-only inspection as exploratory; do not claim quantitative
  surface reconstruction without numerical source data.

### Updated priority

**P1:** coherent signal quality from the 24 numeric Ramsey/spin-echo
measurements, including file-scale normalization and comparisons against
their provided fitted curves.

**P2:** ODMR repeatability grouping with careful matching of sampling,
microwave settings and individual NV identity.

**P3:** inspect scan/profile plot axes to determine if independent numerical
data or suitable calibration exist. No claim of magnetic-field/current-map
reconstruction is presently supported.

This inventory is **metadata plus the first rows of text files**; it does
not analyze the complete numerical signals and does not validate physics.
