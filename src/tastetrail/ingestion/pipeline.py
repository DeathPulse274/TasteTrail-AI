"""Ingestion pipeline: load → normalize → persist parquet."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tastetrail.ingestion.loader import load_raw_dataframe
from tastetrail.ingestion.normalizer import (
    NormalizeStats,
    normalize_dataframe,
    restaurants_to_dataframe,
)

logger = logging.getLogger(__name__)


@dataclass
class IngestSummary:
    """Result of a full ingestion run."""

    output_path: Path
    stats: NormalizeStats
    duration_seconds: float

    def log(self) -> None:
        s = self.stats
        logger.info(
            "Ingest complete: %s rows written to %s (dropped %s: missing=%s, no_city=%s, bad_rating=%s, default_cost_band=%s, unrated=%s) in %.1fs",
            s.output_rows,
            self.output_path,
            s.total_dropped,
            s.dropped_missing_required,
            s.dropped_no_city,
            s.dropped_invalid_rating,
            s.default_cost_band,
            s.unrated_rows,
            self.duration_seconds,
        )


def run_ingestion(output_path: Path, *, skip_load: pd.DataFrame | None = None) -> IngestSummary:
    """
    Load raw data, normalize, and write parquet atomically.

    Args:
        output_path: Destination parquet file.
        skip_load: If provided, use this DataFrame instead of downloading (tests).
    """
    import time

    start = time.perf_counter()
    raw = skip_load if skip_load is not None else load_raw_dataframe()
    result = normalize_dataframe(raw)

    if not result.restaurants:
        raise RuntimeError(
            "No valid restaurants after normalization. "
            "Check dataset schema and normalization rules."
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = restaurants_to_dataframe(result.restaurants)

    tmp_path = output_path.with_suffix(".parquet.tmp")
    df.to_parquet(tmp_path, index=False)
    tmp_path.replace(output_path)

    duration = time.perf_counter() - start
    summary = IngestSummary(
        output_path=output_path,
        stats=result.stats,
        duration_seconds=duration,
    )
    summary.log()
    return summary
