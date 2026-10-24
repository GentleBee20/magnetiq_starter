"""Preview raw ODMR measurements in a ZIP archive."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from zipfile import BadZipFile

from magnetiq.data.preview import preview_odmr
from magnetiq.logging_config import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Log example spectra without altering raw experimental data."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--lines", type=int, default=15)
    args = parser.parse_args()
    configure_logging()
    try:
        result = preview_odmr(args.archive, sample_count=args.samples, line_count=args.lines)
    except (FileNotFoundError, ValueError, BadZipFile, OSError) as exc:
        parser.error(str(exc))

    logger.info("ODMR files found: %d", result.number_of_files)
    logger.info("Measurement groups: %s", result.groups)
    for sample in result.samples:
        logger.info("Measurement: %s", sample.member_name)
        for position, line in enumerate(sample.lines, start=1):
            logger.info("Raw line %02d: %s", position, line)


if __name__ == "__main__":
    main()
