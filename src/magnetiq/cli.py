"""Installed MagnetIQ command-line interface for ODMR fit-quality reports."""

from __future__ import annotations

import argparse
import sys

from scripts.diagnose_odmr import main as diagnose_main


def main() -> None:
    """Dispatch to the existing, validated research-only analysis pipeline."""
    parser = argparse.ArgumentParser(prog="magnetiq")
    subcommands = parser.add_subparsers(dest="command", required=True)
    analyze = subcommands.add_parser("analyze", help="Analyze an ODMR archive")
    analyze.add_argument("archive")
    analyze.add_argument("--limit", type=int, default=0, help="Spectra to analyze; 0 means all")
    analyze.add_argument("--output-dir", default="reports/odmr/experiments")
    analyze.add_argument("--run-name")
    analyze.add_argument("--tracking-uri")
    args = parser.parse_args()
    if args.command == "analyze":
        forwarded = [
            "diagnose_odmr",
            args.archive,
            "--limit",
            str(args.limit),
            "--output-dir",
            args.output_dir,
        ]
        if args.run_name is not None:
            forwarded.extend(["--run-name", args.run_name])
        if args.tracking_uri is not None:
            forwarded.extend(["--tracking-uri", args.tracking_uri])
        sys.argv = forwarded
        diagnose_main()


if __name__ == "__main__":
    main()
