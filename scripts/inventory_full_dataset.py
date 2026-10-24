"""Read-only scientific archive inventory; does not extract files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import struct
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


def _category(name: str) -> str:
    parts = [part.lower() for part in Path(name.replace("\\", "/")).parts]
    for category in ("odmr", "coherence", "profile", "scan"):
        if any(category in part for part in parts):
            return category
    return "other"


def _image_dimensions(data: bytes) -> list[int] | None:
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        return list(struct.unpack(">II", data[16:24]))
    return None


def _inspect_text(data: bytes) -> dict[str, Any]:
    if b"\0" in data:
        return {"sample": "binary_or_nul_containing", "nul_bytes": data.count(b"\0")}
    sample = data[:65536].decode("utf-8-sig", errors="replace")
    lines = [line.strip() for line in sample.splitlines() if line.strip()]
    if not lines:
        return {"sample": "empty"}
    delim = max((",", "\t", ";"), key=lambda d: lines[0].count(d))
    try:
        parsed = list(csv.reader(lines[:15], delimiter=delim))
    except csv.Error as exc:
        return {"sample": "malformed_text", "error": str(exc), "header_sample": lines[:4]}
    header = parsed[0] if parsed else []
    numeric_lines = 0
    widths: list[int] = []
    for row in parsed[1:]:
        widths.append(len(row))
        try:
            if row and all(math_float(field) for field in row):
                numeric_lines += 1
        except ValueError:
            pass
    units = sorted(set(re.findall(r"\[[^\]]{1,25}\]", " ".join(lines[:8]))))
    return {
        "header_sample": lines[:4],
        "delimiter": "tab" if delim == "\t" else delim,
        "columns_first_row": header[:30],
        "sample_numeric_rows": numeric_lines,
        "sample_row_widths": sorted(set(widths)),
        "unit_tokens": units,
        "sample_truncated": len(data) > 65536,
    }


def math_float(value: str) -> bool:
    return bool(value.strip()) and float(value.strip().replace(",", ".")) == float(
        value.strip().replace(",", ".")
    )


def _inspect_zip(zf: zipfile.ZipFile, *, prefix: str = "", depth: int = 0) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = prefix + info.filename
        suffix = Path(info.filename).suffix.lower()
        row: dict[str, Any] = {
            "path": name,
            "category": _category(name),
            "extension": suffix,
            "uncompressed_bytes": info.file_size,
            "compressed_bytes": info.compress_size,
            "nested_depth": depth,
        }
        try:
            with zf.open(info) as stream:
                sample = stream.read(65536)
            if suffix in {".txt", ".csv", ".tsv", ".dat", ".asc"}:
                row["preview"] = _inspect_text(sample)
            elif suffix == ".png":
                row["png_dimensions"] = _image_dimensions(sample)
            elif suffix == ".pdf":
                row["pdf_header"] = sample[:8].decode("latin-1", errors="replace")
            elif suffix == ".zip" and depth < 2 and info.file_size <= 100_000_000:
                with zf.open(info) as nested_stream:
                    nested_data = nested_stream.read()
                with zipfile.ZipFile(io.BytesIO(nested_data)) as nested:
                    row["nested_entries"] = len(nested.infolist())
                    rows.extend(
                        _inspect_zip(nested, prefix=name + "::", depth=depth + 1)
                    )
        except (OSError, ValueError, csv.Error, zipfile.BadZipFile, RuntimeError) as exc:
            row["inspection_error"] = type(exc).__name__ + ": " + str(exc)
        rows.append(row)
    return rows


def inventory(path: Path) -> dict[str, Any]:
    """Inspect metadata and bounded previews without changing source data."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    with zipfile.ZipFile(path) as zf:
        rows = _inspect_zip(zf)
    return {
        "archive": path.name,
        "sha256": digest.hexdigest(),
        "total_entries_including_nested": len(rows),
        "categories": dict(Counter(x["category"] for x in rows)),
        "extensions": dict(Counter(x["extension"] for x in rows)),
        "files": rows,
        "limitations": [
            "Only bounded text previews are inspected; no numerical arrays are modified.",
            "Headers and filename patterns are evidence, not verified scientific meanings.",
            "PNG dimensions do not establish the contents are magnetic-field maps.",
            "PDF content is not interpreted by this inventory.",
            "Nested ZIPs are inspected up to depth 2 if each is below 100 MB.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/dataset_inventory"))
    args = parser.parse_args()
    report = inventory(args.archive)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "full_inventory.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Scientific archive inventory",
        "",
        f"Archive: `{report['archive']}`",
        f"SHA-256: `{report['sha256']}`",
        f"Entries including nested: {report['total_entries_including_nested']}",
        "",
        "## Dataset groups",
        "",
    ]
    lines += [f"- {key}: {count} files" for key, count in sorted(report["categories"].items())]
    lines += ["", "## Files and previews", ""]
    for row in report["files"]:
        details = json.dumps(
            {k: v for k, v in row.items() if k not in ("path", "category")},
            ensure_ascii=False,
        )
        lines.append(f"- **{row['category']}** `{row['path']}`: {details}")
    lines += ["", "## Limitations", ""]
    lines += [f"- {value}" for value in report["limitations"]]
    (args.output_dir / "full_inventory.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("Inventory saved:", args.output_dir / "full_inventory.md")


if __name__ == "__main__":
    main()
