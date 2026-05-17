"""Load raw Zomato data from Hugging Face."""

from __future__ import annotations

import pandas as pd
from datasets import load_dataset

DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"
DATASET_SPLIT = "train"

# Column names in the Hugging Face dataset
COL_URL = "url"
COL_NAME = "name"
COL_ADDRESS = "address"
COL_LOCALITY = "location"
COL_CUISINES = "cuisines"
COL_RATE = "rate"
COL_COST = "approx_cost(for two people)"


def load_raw_dataframe() -> pd.DataFrame:
    """Download (or load from cache) and return the raw dataset as a DataFrame."""
    try:
        dataset = load_dataset(DATASET_NAME, split=DATASET_SPLIT)
    except Exception as exc:  # noqa: BLE001 — wrap HF/network errors
        raise RuntimeError(
            f"Failed to load dataset '{DATASET_NAME}'. "
            "Check your network connection and try again."
        ) from exc
    return dataset.to_pandas()
