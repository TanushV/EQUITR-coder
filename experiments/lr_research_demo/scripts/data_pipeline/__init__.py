"""scripts.data_pipeline package

Expose public helpers for dataset loading/splitting and preprocessing.
"""
from __future__ import annotations

import pathlib
from typing import Tuple

import numpy as np

from .config import load_config
from .ingest import load_and_split, read_raw
from .preprocess import build_preprocessor, fit_and_persist_preprocessor


def get_dataset(cfg: str | pathlib.Path | dict) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Convenience wrapper returning numpy arrays:

    Returns:
        X_train, y_train, X_val, y_val, X_test, y_test
    """
    # load and validate config
    config = load_config(cfg) if not isinstance(cfg, dict) else load_config(cfg)
    train_df, val_df, test_df = load_and_split(config)
    target = config["target_column"]

    def _split_to_arrays(df):
        y = df[target].to_numpy(dtype=np.float64)
        X = df.drop(columns=[target]).to_numpy(dtype=np.float64)
        return X, y

    return (*_split_to_arrays(train_df), *_split_to_arrays(val_df), *_split_to_arrays(test_df))


__all__ = [
    "load_config",
    "read_raw",
    "load_and_split",
    "build_preprocessor",
    "fit_and_persist_preprocessor",
    "get_dataset",
]
