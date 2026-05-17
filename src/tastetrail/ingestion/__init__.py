"""Data ingestion from Hugging Face."""

from tastetrail.ingestion.loader import load_raw_dataframe
from tastetrail.ingestion.normalizer import normalize_dataframe
from tastetrail.ingestion.pipeline import run_ingestion

__all__ = ["load_raw_dataframe", "normalize_dataframe", "run_ingestion"]
