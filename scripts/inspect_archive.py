"""Command-line tool for inventorying scientific ZIP archives."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from zipfile import BadZipFile

from magnetiq.data.archive import inspect
from magnetiq.logging_config import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Inspect the requested archive and write a machine-readable manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()
    configure_logging()

    try:
        result = inspect(args.archive, args.output_dir)
    except (FileNotFoundError, ValueError, BadZipFile, OSError) as exc:
        parser.error(str(exc))

    logger.info("Found %d files", result["n_files"])
    logger.info("File extensions: %s", result["extensions"])
    for entry in result["files"][:30]:
        logger.info("File: %s | Size: %d bytes", entry["name"], entry["bytes"])
    logger.info("Full manifest: %s", args.output_dir / "archive_inventory.csv")


if __name__ == "__main__":
    main()
