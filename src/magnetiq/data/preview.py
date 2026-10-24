"""Safe, read-only previews of measurements stored in scientific ZIP archives."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile, is_zipfile


@dataclass(frozen=True)
class MeasurementPreview:
    """Raw lines from one archived measurement, without implicit parsing."""

    member_name: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class PreviewSummary:
    """ODMR directory counts and representative files."""

    number_of_files: int
    groups: dict[str, int]
    samples: tuple[MeasurementPreview, ...]


def preview_odmr(
    archive_path: Path, *, sample_count: int = 3, line_count: int = 15
) -> PreviewSummary:
    """Inspect ODMR text-file structure without extracting the archive.

    Raw lines use repr-safe escaping so delimiters, headers, and line endings
    remain visible. A strict UTF-8 decode exposes unexpected encodings.
    """
    if sample_count < 1 or line_count < 1:
        raise ValueError("sample_count and line_count must be positive")
    if not archive_path.is_file():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    if not is_zipfile(archive_path):
        raise ValueError(f"Not a valid ZIP archive: {archive_path}")

    with ZipFile(archive_path) as archive:
        members = sorted(
            member
            for member in archive.namelist()
            if "/ODMR/" in member and member.lower().endswith(".txt")
        )
        groups = dict(sorted(Counter(Path(member).parent.name for member in members).items()))
        samples: list[MeasurementPreview] = []
        for name in members[:sample_count]:
            with archive.open(name) as stream:
                lines = tuple(
                    repr(raw.rstrip(b"\r\n"))
                    for _, raw in zip(range(line_count), stream)
                )
            samples.append(MeasurementPreview(name, lines))
    return PreviewSummary(len(members), groups, tuple(samples))
