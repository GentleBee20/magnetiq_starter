"""Dataset-wide schema and integrity audit for real ODMR measurements."""

from __future__ import annotations

import csv
import statistics
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

from magnetiq.data.odmr import list_odmr_members, read_odmr


@dataclass(frozen=True)
class AuditRecord:
    """Summary and validity of one archived measurement."""

    source: str
    status: str
    samples: int
    start_ghz: float | None
    stop_ghz: float | None
    median_step_mhz: float | None
    contrast_min: float | None
    contrast_max: float | None
    reason: str


def audit_odmr(archive_path: Path) -> list[AuditRecord]:
    """Audit all ODMR files independently, retaining invalid-file reasons."""
    records: list[AuditRecord] = []
    with ZipFile(archive_path) as archive:
        for member in list_odmr_members(archive):
            try:
                spectrum = read_odmr(archive, member)
                frequencies = spectrum.frequency_ghz
                steps_mhz = [
                    (b - a) * 1000
                    for a, b in zip(frequencies, frequencies[1:])
                ]
                records.append(
                    AuditRecord(
                        source=member,
                        status="VALID",
                        samples=spectrum.count,
                        start_ghz=frequencies[0],
                        stop_ghz=frequencies[-1],
                        median_step_mhz=statistics.median(steps_mhz),
                        contrast_min=min(spectrum.normalized_contrast),
                        contrast_max=max(spectrum.normalized_contrast),
                        reason="",
                    )
                )
            except (ValueError, UnicodeError, KeyError, OSError) as exc:
                records.append(
                    AuditRecord(member, "INVALID", 0, None, None, None, None, None, str(exc))
                )
    return records


def write_audit(records: list[AuditRecord], output: Path) -> None:
    """Write a reproducible CSV audit outside the raw dataset."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "source", "status", "samples", "start_ghz", "stop_ghz",
                "median_step_mhz", "contrast_min", "contrast_max", "reason",
            ]
        )
        for record in records:
            writer.writerow(
                [
                    record.source, record.status, record.samples, record.start_ghz,
                    record.stop_ghz, record.median_step_mhz, record.contrast_min,
                    record.contrast_max, record.reason,
                ]
            )
