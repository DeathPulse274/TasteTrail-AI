#!/usr/bin/env python3
"""Ingest Zomato dataset from Hugging Face into processed parquet."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Allow running as script without editable install
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from tastetrail.config import get_settings
from tastetrail.ingestion.pipeline import run_ingestion


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Zomato data into parquet")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output parquet path (default: DATA_PATH from settings)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    settings = get_settings()
    output = args.output or settings.data_path

    try:
        summary = run_ingestion(output)
    except Exception as exc:
        logging.error("%s", exc)
        return 1

    s = summary.stats
    print(f"Wrote {s.output_rows} restaurants to {summary.output_path}")
    print(
        f"Dropped {s.total_dropped} rows "
        f"(missing={s.dropped_missing_required}, no_city={s.dropped_no_city}, "
        f"bad_rating={s.dropped_invalid_rating})"
    )
    print(f"Unrated rows kept: {s.unrated_rows}, default cost band: {s.default_cost_band}")
    print(f"Duration: {summary.duration_seconds:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
