"""Run the existing ODMR fit diagnostics and report workflow."""

from __future__ import annotations

import csv
import logging
from dataclasses import asdict
from pathlib import Path
from zipfile import ZipFile

import mlflow

from magnetiq.data.odmr import OdmrSpectrum, list_odmr_members, read_odmr
from magnetiq.logging_config import configure_logging
from magnetiq.processing.diagnostics import choose_fit, diagnose_fit
from magnetiq.processing.resonance import fit_spectrum
from magnetiq.reporting.fit_plots import plot_batch, plot_fit
from magnetiq.reporting.mvp_report import write_measurement_report
from magnetiq.tracking import (
    file_sha256,
    new_run_location,
    summarize_rows,
    tracked_run,
    write_manifest,
)

logger = logging.getLogger(__name__)


def run_analysis(
    archive: Path,
    *,
    limit: int = 0,
    output_dir: Path = Path("reports/odmr/experiments"),
    run_name: str | None = None,
    tracking_uri: str | None = None,
) -> Path:
    """Run an immutable ODMR fit-quality experiment and return its report directory."""
    if limit < 0:
        raise ValueError("limit must be nonnegative")
    configure_logging()
    with ZipFile(archive) as dataset:
        members = list_odmr_members(dataset)
        if limit:
            members = members[:limit]
        spectra = [read_odmr(dataset, member) for member in members]
    location = new_run_location(output_dir, run_name, tracking_uri)
    with tracked_run(
        location, archive, limit=limit, spectrum_count=len(spectra)
    ) as run_id:
        analyze_and_log(spectra, location.output_dir, run_id, location.tracking_uri, archive)
    logger.info("MLflow run %s | directory %s", run_id, location.output_dir)
    return location.output_dir


def analyze_and_log(
    spectra: list[OdmrSpectrum],
    output_dir: Path,
    run_id: str,
    tracking_uri: str,
    archive: Path,
) -> None:
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
    write_measurement_report(results, output_dir)
    metrics = summarize_rows([asdict(result) for result in results])
    mlflow.log_metrics(metrics)
    write_manifest(
        output_dir / "manifest.json",
        run_id=run_id,
        tracking_uri=tracking_uri,
        archive_sha256=file_sha256(archive),
    )
    logger.info("Wrote diagnostics for %d spectra to %s", len(results), output_dir)
    logger.info("Statuses are experimental FIT diagnostics, NOT physical anomaly labels")

