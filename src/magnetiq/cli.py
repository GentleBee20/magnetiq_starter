"""Installed command-line interface for provisional ODMR measurement reports."""

from __future__ import annotations

import argparse
from pathlib import Path

from magnetiq.analysis import run_analysis


def main() -> None:
    """Run supported MagnetIQ analysis commands."""
    parser = argparse.ArgumentParser(prog="magnetiq")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser("analyze", help="Analyze ODMR measurements in a ZIP archive")
    analyze.add_argument("archive", type=Path)
    analyze.add_argument("--limit", type=int, default=0, help="Number of spectra; 0 means all")
    analyze.add_argument("--output-dir", type=Path, default=Path("reports/odmr/experiments"))
    analyze.add_argument("--run-name")
    analyze.add_argument("--tracking-uri")
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be nonnegative")
    if args.command == "analyze":
        location = run_analysis(
            args.archive,
            limit=args.limit,
            output_dir=args.output_dir,
            run_name=args.run_name,
            tracking_uri=args.tracking_uri,
        )
        print(f"Measurement report: {location / 'measurement_report.html'}")
        print(f"Machine-readable report: {location / 'measurement_report.json'}")


if __name__ == "__main__":
    main()
