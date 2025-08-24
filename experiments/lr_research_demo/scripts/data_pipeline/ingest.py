"""Ingest utilities: read raw dataset and perform deterministic train/val/test splits.

Public API:
- read_raw(path: str|Path) -> pandas.DataFrame
- load_and_split(config: dict|str|Path) -> (train_df, val_df, test_df)

Config can be a mapping or a path to YAML/JSON and is validated by load_config from config.py.
"""
from __future__ import annotations

import pathlib
from typing import Tuple, Optional

import pandas as pd
from sklearn.model_selection import train_test_split

from .config import load_config, ConfigError


def read_raw(path: str | pathlib.Path) -> pd.DataFrame:
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset file not found: {p}")
    # Let pandas infer dtypes but enforce float64 for numeric columns later
    df = pd.read_csv(p, encoding="utf-8")
    return df


def _maybe_cast_numeric(df: pd.DataFrame, numeric_columns: Optional[list]) -> pd.DataFrame:
    if not numeric_columns:
        return df
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].astype("float64")
    return df


def load_and_split(cfg: dict | str | pathlib.Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load dataset and return (train_df, val_df, test_df).

    Behavior:
    - If cfg is a path, it is parsed via load_config.
    - Validates presence of target_column.
    - Performs deterministic splits using sklearn.train_test_split with random_state=config.random_seed.
    - If stratify is True or a column name, performs stratified splits on that column.
    """
    config = load_config(cfg) if not isinstance(cfg, dict) else load_config(cfg)
    path = pathlib.Path(config["path"]).expanduser().resolve()
    df = read_raw(path)

    # ensure target exists
    target = config["target_column"]
    if target not in df.columns:
        raise ConfigError(f"target_column '{target}' not found in dataset")

    # optional casting
    df = _maybe_cast_numeric(df, config.get("numeric_columns"))

    # compute splits
    train_frac = float(config["split"]["train"])
    val_frac = float(config["split"]["val"])
    test_frac = float(config["split"]["test"])

    rs = int(config.get("random_seed", 42))

    stratify_col = None
    stratify = config.get("stratify", False)
    if stratify:
        if isinstance(stratify, str):
            stratify_col = stratify
        elif isinstance(stratify, bool) and stratify is True:
            stratify_col = target
        else:
            stratify_col = None

    # First split off test set
    train_val_df, test_df = train_test_split(
        df,
        test_size=test_frac,
        random_state=rs,
        shuffle=True,
        stratify=(df[stratify_col] if stratify_col in df.columns else None) if stratify_col else None,
    )

    # Then split train and val from remaining
    # new val fraction relative to train_val
    rel_val = val_frac / (train_frac + val_frac)
    train_df, val_df = train_test_split(
        train_val_df,
        test_size=rel_val,
        random_state=rs,
        shuffle=True,
        stratify=(train_val_df[stratify_col] if stratify_col in train_val_df.columns else None) if stratify_col else None,
    )

    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)
