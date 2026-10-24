"""Backward-compatible CLI for provisional ODMR fit diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

from magnetiq.analysis import run_analysis


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--limit", type=int, default=6, help="Number of spectra; 0 means all")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/odmr/experiments"))
    parser.add_argument("--run-name", type=str, default=None)
    parser.add_argument("--tracking-uri", type=str, default=None)
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be nonnegative")
    run_analysis(
        args.archive,
        limit=args.limit,
        output_dir=args.output_dir,
        run_name=args.run_name,
        tracking_uri=args.tracking_uri,
    )


if __name__ == "__main__":
    main()
