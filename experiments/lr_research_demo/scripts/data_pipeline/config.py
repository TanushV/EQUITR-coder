"""Load and validate dataset configuration (YAML/JSON or dict).

Expected keys (example):
path: path/to/dataset.csv
target_column: y
split:
  train: 0.8
  val: 0.1
  test: 0.1
random_seed: 42
stratify: false  # or column name
artifacts_dir: experiments/artifacts
numeric_columns: [f1, f2, f3]
categorical_columns: []
"""
from __future__ import annotations

import pathlib
import json
from typing import Any, Dict

import yaml


DEFAULTS: Dict[str, Any] = {
    "split": {"train": 0.8, "val": 0.1, "test": 0.1},
    "random_seed": 42,
    "stratify": False,
    "artifacts_dir": "experiments/artifacts",
    "numeric_columns": None,
    "categorical_columns": None,
}


class ConfigError(ValueError):
    pass


def _load_file(path: pathlib.Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() in {".yml", ".yaml"}:
            return yaml.safe_load(text) or {}
        elif path.suffix.lower() == ".json":
            return json.loads(text)
        else:
            # try YAML first
            return yaml.safe_load(text) or {}
    except Exception as exc:  # pragma: no cover - manifest errors bubble up
        raise ConfigError(f"Failed to parse config file {path}: {exc}") from exc


def load_config(obj: str | pathlib.Path | Dict[str, Any]) -> Dict[str, Any]:
    """Load config from path (YAML/JSON) or return a validated copy of mapping.

    Returns a new dict with defaults applied and normalized paths resolved.
    """
    if isinstance(obj, (str, pathlib.Path)):
        p = pathlib.Path(obj).expanduser().resolve()
        cfg = _load_file(p)
    elif isinstance(obj, dict):
        cfg = obj.copy()
    else:
        raise ConfigError("config must be a path or a mapping")

    # apply defaults
    merged: Dict[str, Any] = {}
    merged.update(DEFAULTS)
    merged.update(cfg)

    # basic required keys
    if "path" not in merged:
        raise ConfigError("Missing required key: path")
    if "target_column" not in merged:
        raise ConfigError("Missing required key: target_column")

    # validate splits
    split = merged.get("split")
    try:
        t = float(split.get("train"))
        v = float(split.get("val"))
        ts = float(split.get("test"))
    except Exception:
        raise ConfigError("split.train, split.val and split.test must be numbers")

    if not (0.0 < t < 1.0 and 0.0 < v < 1.0 and 0.0 < ts < 1.0):
        raise ConfigError("Each split must be in (0,1)")

    if round(t + v + ts, 3) != 1.0:
        raise ConfigError("sum of splits must be 1.0 (within rounding 1e-3)")

    # artifacts dir
    merged["artifacts_dir"] = str(pathlib.Path(merged.get("artifacts_dir")).as_posix())

    # numeric/categorical normalization (allow None)
    if merged.get("numeric_columns") is None:
        merged["numeric_columns"] = []
    if merged.get("categorical_columns") is None:
        merged["categorical_columns"] = []

    # random seed
    try:
        merged["random_seed"] = int(merged.get("random_seed") or DEFAULTS["random_seed"])
    except Exception:
        raise ConfigError("random_seed must be an integer")

    return merged
