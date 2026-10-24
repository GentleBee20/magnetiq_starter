"""Inventory ZIP archives without extracting untrusted contents."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import TypedDict
from zipfile import ZipFile, is_zipfile


class ArchiveEntry(TypedDict):
    """Serializable information about a single archive member."""

    name: str
    bytes: int
    compressed_bytes: int
    extension: str
    encrypted: bool


class ArchiveInventory(TypedDict):
    """Summary and file-level metadata for an archive."""

    source_archive: str
    archive_size_bytes: int
    n_files: int
    extensions: dict[str, int]
    files: list[ArchiveEntry]


def inspect_archive(path: Path) -> ArchiveInventory:
    """Inspect an archive, returning metadata without extracting files.

    Raises:
        FileNotFoundError: Archive path does not exist.
        ValueError: Archive is not a readable ZIP file.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Archive not found: {path}")
    if not is_zipfile(path):
        raise ValueError(f"Not a valid ZIP archive: {path}")

    with ZipFile(path) as archive:
        entries: list[ArchiveEntry] = [
            {
                "name": info.filename,
                "bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "extension": Path(info.filename).suffix.lower() or "(none)",
                "encrypted": bool(info.flag_bits & 0x1),
            }
            for info in archive.infolist()
            if not info.is_dir()
        ]

    return {
        "source_archive": path.name,
        "archive_size_bytes": path.stat().st_size,
        "n_files": len(entries),
        "extensions": dict(sorted(Counter(e["extension"] for e in entries).items())),
        "files": entries,
    }


def write_inventory(inventory: ArchiveInventory, output_dir: Path) -> tuple[Path, Path]:
    """Persist a manifest as JSON and CSV for downstream analysis."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "archive_inventory.json"
    csv_path = output_dir / "archive_inventory.csv"

    json_path.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["name", "bytes", "compressed_bytes", "extension", "encrypted"]
        )
        writer.writeheader()
        writer.writerows(inventory["files"])
    return json_path, csv_path


def inspect(path: Path, out_dir: Path) -> ArchiveInventory:
    """Compatibility API: inspect an archive and write its manifest."""
    inventory = inspect_archive(path)
    write_inventory(inventory, out_dir)
    return inventory
