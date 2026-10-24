"""Analyze real ODMR spectra using model-free metrics and plot examples."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from magnetiq.data.odmr import list_odmr_members, read_odmr
from magnetiq.logging_config import configure_logging
from magnetiq.processing.summary import summarize_spectrum
from magnetiq.reporting.spectra import plot_spectra, write_summaries

logger = logging.getLogger(__name__)


def main() -> None:
    """Summarize every spectrum and save representative experimental figures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/odmr"))
    parser.add_argument("--plot-count", type=int, default=6)
    args = parser.parse_args()
    configure_logging()

    if args.plot_count < 1:
        parser.error("--plot-count must be positive")
    try:
        with ZipFile(args.archive) as archive:
            names = list_odmr_members(archive)
            spectra = [read_odmr(archive, name) for name in names]
        if not spectra:
            parser.error("No ODMR spectra found in archive")
        summaries = [summarize_spectrum(spectrum) for spectrum in spectra]
        csv_path = args.output_dir / "spectrum_summary.csv"
        plot_path = args.output_dir / "representative_spectra.png"
        write_summaries(summaries, csv_path)
        plot_spectra(spectra[: args.plot_count], plot_path)
    except (OSError, BadZipFile, ValueError, UnicodeError) as exc:
        parser.error(str(exc))

    logger.info("Analyzed %d real ODMR spectra", len(spectra))
    logger.info("Summary: %s", csv_path)
    logger.info("Comparison figure: %s", plot_path)
    logger.info("Minimum locations are NOT validated resonance estimates")


if __name__ == "__main__":
    main()
