"""Preprocessing helpers: build a ColumnTransformer and fit/save it.

Public API:
- build_preprocessor(numeric_columns, categorical_columns) -> sklearn.compose.ColumnTransformer
- fit_and_persist_preprocessor(preprocessor, train_df, artifacts_dir: str|Path) -> Path (path to saved file)

Notes:
- Uses SimpleImputer + StandardScaler for numeric columns
- Uses SimpleImputer (constant) + OneHotEncoder for categorical columns
- Saves transformer with pickle to artifacts_dir/preprocessor.joblib
"""
from __future__ import annotations

import pathlib
import pickle
from typing import Iterable

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def _ensure_list(cols: Iterable | None) -> list:
    if cols is None:
        return []
    return list(cols)


def build_preprocessor(numeric_columns: Iterable | None, categorical_columns: Iterable | None) -> ColumnTransformer:
    num_cols = _ensure_list(numeric_columns)
    cat_cols = _ensure_list(categorical_columns)

    transformers = []
    if num_cols:
        num_pipeline = ("num", SimpleImputer(strategy="mean"), num_cols)
        # we'll wrap scaling at ColumnTransformer level using a pipeline styled tuple
        transformers.append(("num", StandardScaler(), num_cols))
    if cat_cols:
        # Impute missing categorical values then one-hot encode
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse=False), cat_cols))

    # If both empty, create a passthrough transformer
    if not transformers:
        return ColumnTransformer(transformers=[("passthrough", "passthrough", [])], remainder="drop")

    # For numeric we want imputation then scaling; but ColumnTransformer takes final transformers.
    # To keep dependencies minimal we implement numeric as StandardScaler (assumes no NaNs) and
    # require upstream code to impute if needed. However, to keep it correct, we'll create simple
    # transformers using pipelines only if sklearn.pipeline is available.
    from sklearn.pipeline import Pipeline

    new_transformers = []
    if num_cols:
        num_pipeline = Pipeline([("imputer", SimpleImputer(strategy="mean")), ("scale", StandardScaler())])
        new_transformers.append(("num", num_pipeline, num_cols))
    if cat_cols:
        cat_pipeline = Pipeline([("imputer", SimpleImputer(strategy="constant", fill_value="")), ("ohe", OneHotEncoder(handle_unknown="ignore", sparse=False))])
        new_transformers.append(("cat", cat_pipeline, cat_cols))

    ct = ColumnTransformer(transformers=new_transformers, remainder="drop", sparse_threshold=0.0)
    return ct


def fit_and_persist_preprocessor(preprocessor: ColumnTransformer, train_df: pd.DataFrame, artifacts_dir: str | pathlib.Path) -> pathlib.Path:
    artifacts_dir = pathlib.Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    # Fit on train
    # Select columns that the transformer expects
    cols = []
    for name, trans, col in preprocessor.transformers:
        if col == "remainder":
            continue
        cols.extend(col if isinstance(col, (list, tuple)) else [col])
    # Deduplicate while preserving order
    seen = set()
    cols = [c for c in cols if not (c in seen or seen.add(c))]
    X_train = train_df[cols] if cols else train_df
    preprocessor.fit(X_train)
    out_path = artifacts_dir / "preprocessor.joblib"
    # Use pickle to avoid adding joblib dependency
    with open(out_path, "wb") as f:
        pickle.dump(preprocessor, f, protocol=pickle.HIGHEST_PROTOCOL)
    return out_path
