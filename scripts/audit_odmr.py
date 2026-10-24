"""Audit every ODMR measurement and save a schema/integrity report."""

from __future__ import annotations

import argparse
import logging
from collections import Counter
from pathlib import Path
from zipfile import BadZipFile

from magnetiq.data.audit import audit_odmr, write_audit
from magnetiq.logging_config import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the audit and summarize unexpected formats or values."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, default=Path("reports/odmr_schema_audit.csv"))
    args = parser.parse_args()
    configure_logging()
    try:
        records = audit_odmr(args.archive)
        write_audit(records, args.output)
    except (OSError, BadZipFile) as exc:
        parser.error(str(exc))
    counts = Counter(record.status for record in records)
    logger.info("Audited %d ODMR files: %s", len(records), dict(counts))
    for record in records:
        if record.status != "VALID":
            logger.warning("Invalid measurement %s: %s", record.source, record.reason)
    logger.info("Audit results saved to %s", args.output)


if __name__ == "__main__":
    main()
