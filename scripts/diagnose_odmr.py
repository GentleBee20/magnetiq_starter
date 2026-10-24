"""Generate provisional ODMR fit diagnostics, overlays and summary plots."""

from __future__ import annotations

import argparse
import csv
import logging
from dataclasses import asdict
from pathlib import Path
from zipfile import ZipFile

from magnetiq.data.odmr import OdmrSpectrum, list_odmr_members, read_odmr
from magnetiq.logging_config import configure_logging
from magnetiq.processing.diagnostics import choose_fit, diagnose_fit
from magnetiq.processing.resonance import fit_spectrum
from magnetiq.reporting.fit_plots import plot_batch, plot_fit
from magnetiq.tracking import file_sha256, new_run_location, summarize_rows, tracked_run, write_manifest

import mlflow

logger = logging.getLogger(__name__)


def main() -> None:
    """Fit selected spectra, saving diagnostic evidence and not hardware verdicts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--limit", type=int, default=6, help="Number of spectra; 0 means all")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/odmr/experiments"))
    parser.add_argument("--run-name", type=str, default=None)
    parser.add_argument("--tracking-uri", type=str, default=None)
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be nonnegative")
    configure_logging()
    with ZipFile(args.archive) as archive:
        members = list_odmr_members(archive)
        if args.limit:
            members = members[: args.limit]
        spectra = [read_odmr(archive, member) for member in members]
    location = new_run_location(args.output_dir, args.run_name, args.tracking_uri)
    with tracked_run(location, args.archive, limit=args.limit, spectrum_count=len(spectra)) as run_id:
        analyze_and_log(spectra, location.output_dir, run_id, location.tracking_uri, args.archive)
    logger.info("MLflow run %s | directory %s", run_id, location.output_dir)


def analyze_and_log(spectra: list[OdmrSpectrum], output_dir: Path, run_id: str,
                    tracking_uri: str, archive: Path) -> None:
    """Create deterministic reports inside a uniquely allocated run directory."""
    results = []
    for index, spectrum in enumerate(spectra, start=1):
        fits = [fit_spectrum(spectrum, n) for n in (0, 1, 2)]
        diagnosis = diagnose_fit(spectrum, fits)
        results.append(diagnosis)
        plot_fit(
            spectrum,
            choose_fit(fits),
            diagnosis,
            output_dir / "plots" / f"{index:03d}_{Path(spectrum.source).stem}.png",
        )
        logger.info("%s: %s (%s)", spectrum.source, diagnosis.status, diagnosis.model)
    csv_path = output_dir / "fit_diagnostics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        if results:
            writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0])))
            writer.writeheader()
            for result in results:
                row = asdict(result)
                row["warnings"] = ";".join(result.warnings)
                writer.writerow(row)
    plot_batch(results, output_dir / "summary.png")
    metrics = summarize_rows([asdict(result) for result in results])
    mlflow.log_metrics(metrics)
    write_manifest(
        output_dir / "manifest.json", run_id=run_id, tracking_uri=tracking_uri,
        archive_sha256=file_sha256(archive),
    )
    logger.info("Wrote diagnostics for %d spectra to %s", len(results), output_dir)
    logger.info("Statuses are experimental FIT diagnostics, NOT physical anomaly labels")


if __name__ == "__main__":
    main()
