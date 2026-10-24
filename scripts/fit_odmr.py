"""Compare baseline, single- and double-Lorentzian fits on real ODMR data."""

from __future__ import annotations

import argparse
import csv
import logging
from pathlib import Path
from zipfile import ZipFile

from magnetiq.data.odmr import list_odmr_members, read_odmr
from magnetiq.logging_config import configure_logging
from magnetiq.processing.resonance import fit_spectrum

logger = logging.getLogger(__name__)


def main() -> None:
    """Fit sample spectra, exporting model-comparison metrics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--output", type=Path, default=Path("reports/odmr/model_fits.csv"))
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    configure_logging()
    with ZipFile(args.archive) as archive:
        names = list_odmr_members(archive)[: args.limit]
        spectra = [read_odmr(archive, name) for name in names]
    rows = []
    for spectrum in spectra:
        fits = [fit_spectrum(spectrum, peaks) for peaks in (0, 1, 2)]
        for fit in fits:
            rows.append(
                {
                    "source": fit.source,
                    "model": fit.model,
                    "success": fit.success,
                    "rmse": fit.rmse,
                    "aicc": fit.aicc,
                    "parameters": repr(fit.parameters),
                    "reason": fit.reason,
                }
            )
        successful = [fit for fit in fits if fit.success]
        if successful:
            chosen = min(successful, key=lambda fit: fit.aicc)
            logger.info(
                "%s: preferred candidate %s (AICc %.2f)", spectrum.source, chosen.model, chosen.aicc
            )
        else:
            logger.warning("%s: no successful fits", spectrum.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source", "model", "success", "rmse", "aicc", "parameters", "reason"],
        )
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Saved %d model-fitting records to %s", len(rows), args.output)
    logger.info("Model preference is NOT a scientific measurement-quality verdict")


if __name__ == "__main__":
    main()
