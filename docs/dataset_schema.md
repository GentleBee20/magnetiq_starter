# Dataset schema — NV-center ODMR measurements

Source: [Zenodo 14697917](https://doi.org/10.5281/zenodo.14697917).
This dataset must be downloaded by users; the repository does not redistribute it.

## Observed inventory (2026-10-24)

- ZIP archive: 152 files (129 TXT, 20 PNG, 2 PDF, 1 nested ZIP).
- `Data/ODMR/`: 105 text spectra across Hole2 (5), Hole3 (23), Hole4 (21), NoHole2 (22), NoHole3 (24), NoHole5 (10).
- All 105 ODMR text files passed structural checks locally.
- Header: `Freq [GHz],Normalized readout contrast`.
- Numeric frequency (GHz) and dimensionless normalized contrast; frequency strictly ascending within each file.
- Example initial frequency: 2.85 GHz; example step: 0.0001 GHz = 0.1 MHz.
- Filenames encode experimental group, timestamp, microwave settings and an NV identifier. Treat these as *filename metadata* pending confirmation against authors' documentation.

## Interpretation and limitations

The **VALID** status from `audit_odmr.py` means parsable, finite, monotonically
increasing frequency and at least two rows. It does **not** prove an ODMR
resonance exists or that a measurement is scientifically reliable.
File prefixes `Hole` and `NoHole` should not be assigned causal
interpretations without reading experimental methods.

Generated inventory and per-file audit reports are written in `reports/`
and excluded from Git. Raw data live in `data/raw/` and are excluded from Git.

Next: model-free visualization and preliminary signal diagnostics; compare
resonance models only after inspecting representative complete spectra.
