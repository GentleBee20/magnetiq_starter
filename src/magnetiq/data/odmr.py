"""Validated loading of experimental ODMR frequency sweeps."""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

HEADER = ("Freq [GHz]", "Normalized readout contrast")


@dataclass(frozen=True)
class OdmrSpectrum:
    """An unmodified frequency sweep, preserving physical units."""

    source: str
    frequency_ghz: tuple[float, ...]
    normalized_contrast: tuple[float, ...]

    @property
    def count(self) -> int:
        return len(self.frequency_ghz)


def parse_odmr(text: str, *, source: str = "<memory>") -> OdmrSpectrum:
    """Parse a spectrum, rejecting invalid rows rather than silently cleaning."""
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if header is None or tuple(value.strip() for value in header) != HEADER:
        raise ValueError(f"{source}: unexpected ODMR header: {header!r}")

    frequencies: list[float] = []
    contrasts: list[float] = []
    for line_number, row in enumerate(reader, start=2):
        if len(row) != 2:
            raise ValueError(f"{source}:{line_number}: expected two columns")
        try:
            frequency, contrast = (float(value.strip()) for value in row)
        except ValueError as exc:
            raise ValueError(f"{source}:{line_number}: nonnumeric measurement") from exc
        if not math.isfinite(frequency) or not math.isfinite(contrast):
            raise ValueError(f"{source}:{line_number}: nonfinite measurement")
        frequencies.append(frequency)
        contrasts.append(contrast)

    if len(frequencies) < 2:
        raise ValueError(f"{source}: at least two measurement rows are required")
    if any(end <= start for start, end in zip(frequencies, frequencies[1:])):
        raise ValueError(f"{source}: frequencies must be strictly increasing")
    return OdmrSpectrum(source, tuple(frequencies), tuple(contrasts))


def read_odmr(archive: ZipFile, member_name: str) -> OdmrSpectrum:
    """Read one spectrum directly from an archive without extraction."""
    with archive.open(member_name) as handle:
        contents = handle.read().decode("utf-8-sig")
    return parse_odmr(contents, source=member_name)


def list_odmr_members(archive: ZipFile) -> list[str]:
    """Return sorted ODMR text members, excluding unrelated experiments."""
    return sorted(
        info.filename
        for info in archive.infolist()
        if not info.is_dir()
        and "/ODMR/" in info.filename
        and Path(info.filename).suffix.lower() == ".txt"
    )
