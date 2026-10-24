"""Compare two immutable MagnetIQ diagnostic runs using per-spectrum CSV records."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_results(path: Path) -> dict[str, dict[str, str]]:
    """Read a run by its unique spectrum source identifier."""
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result = {row["source"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate spectrum source in {path}")
    return result


def main() -> None:
    """Compare status transitions on identical spectra and optional provenance."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path, help="Old fit_diagnostics.csv")
    parser.add_argument("after", type=Path, help="New fit_diagnostics.csv")
    parser.add_argument("--output", type=Path, help="Optional path for comparison CSV")
    args = parser.parse_args()

    before = read_results(args.before)
    after = read_results(args.after)
    if set(before) != set(after):
        raise ValueError(
            f"Runs have different spectra: before-only={len(set(before) - set(after))}, "
            f"after-only={len(set(after) - set(before))}. Compare identical cohorts."
        )
    changes = [
        {
            "source": source,
            "before_status": before[source]["status"],
            "after_status": after[source]["status"],
            "before_warnings": before[source].get("warnings", ""),
            "after_warnings": after[source].get("warnings", ""),
            "before_model": before[source].get("model", ""),
            "after_model": after[source].get("model", ""),
        }
        for source in sorted(before)
    ]
    fields = list(changes[0]) if changes else []
    output = args.output or args.after.with_name("comparison.csv")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an existing comparison: {output}")
    with output.open("w", newline="", encoding="utf-8") as handle:
        if fields:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(changes)
    transitions: dict[str, int] = {}
    for row in changes:
        key = f"{row['before_status']} -> {row['after_status']}"
        transitions[key] = transitions.get(key, 0) + 1
    print(json.dumps({"compared": len(changes), "transitions": transitions, "csv": str(output)}, indent=2))


if __name__ == "__main__":
    main()
