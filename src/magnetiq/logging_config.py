"""Consistent command-line logging. Libraries must never configure root logging."""

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure logging once at the application entry point."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
