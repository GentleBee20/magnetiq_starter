"""Inventory a research ZIP archive without extracting any contents."""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from zipfile import BadZipFile, ZipFile


def inspect(path: Path, out_dir: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Archive not found: {path}")
    if not ZipFile.is_zipfile(path):
        raise ValueError(f"Not a valid ZIP archive: {path}")

    with ZipFile(path) as archive:
        entries = []
        for info in archive.infolist():
            if info.is_dir():
                continue
            entries.append({
                "name": info.filename,
                "bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "extension": Path(info.filename).suffix.lower() or "(none)",
                "encrypted": bool(info.flag_bits & 0x1),
            })
    summary = {
        "source_archive": path.name,
        "archive_size_bytes": path.stat().st_size,
        "n_files": len(entries),
        "extensions": dict(sorted(Counter(e["extension"] for e in entries).items())),
        "files": entries,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "archive_inventory.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out_dir / "archive_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "bytes", "compressed_bytes", "extension", "encrypted"])
        writer.writeheader()
        writer.writerows(entries)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()
    try:
        result = inspect(args.archive, args.output_dir)
    except (FileNotFoundError, ValueError, BadZipFile) as exc:
        parser.error(str(exc))
    print(f"Files: {result['n_files']}")
    print("Extensions:", result["extensions"])
    print("First 30 filenames:")
    for item in result["files"][:30]:
        print(f"  {item['name']} ({item['bytes']:,} bytes)")
    print(f"Full manifest: {args.output_dir / 'archive_inventory.csv'}")


if __name__ == "__main__":
    main()
