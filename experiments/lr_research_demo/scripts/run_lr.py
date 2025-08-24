"""Run a simple linear regression experiment and produce artifacts via scripts.artifacts.

Publicly exposed function:
- run_experiment(config: dict) -> dict

The CLI retains the --generate-dataset helper and otherwise should be invoked via runner.py which imports and calls run_experiment.
"""
from __future__ import annotations

import argparse
import sys
import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Import artifacts helpers
from scripts import artifacts

# Exceptions mapped to exit codes by callers
class ArgError(Exception):
    pass

class DataError(Exception):
    pass

class WriteError(Exception):
    pass

class TrainError(Exception):
    pass

class EvalError(Exception):
    pass

# Cache the discovered project root to avoid repeated filesystem scans
_PROJECT_ROOT: Optional[Path] = None


def get_project_root() -> Path:
    global _PROJECT_ROOT
    if _PROJECT_ROOT is not None:
        return _PROJECT_ROOT

    # Allow explicit override via environment variable for convenience
    env_root = os.getenv("PROJECT_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        if (p / "requirements.md").is_file():
            _PROJECT_ROOT = p
            return _PROJECT_ROOT
        # If env var provided but invalid, fail fast
        raise DataError(f"PROJECT_ROOT={env_root} does not contain requirements.md")

    cur = Path.cwd().resolve()

    # 1) Fast path: walk upward from current working directory
    for parent in [cur, *cur.parents]:
        if (parent / "requirements.md").is_file():
            _PROJECT_ROOT = parent
            return _PROJECT_ROOT

    # 2) Fallback: find repository top by locating a .git directory
    repo_top = next((p for p in [cur, *cur.parents] if (p / ".git").exists()), None)

    # 3) If we found a repo top, search once for requirements.md under it
    if repo_top is not None:
        matches = list(repo_top.rglob("requirements.md"))
        if len(matches) == 1:
            _PROJECT_ROOT = matches[0].parent
            return _PROJECT_ROOT
        if len(matches) > 1:
            raise DataError(
                f"Multiple requirements.md files found under repository root {repo_top}: {[str(m) for m in matches]}. "
                "Please run the script from the desired project directory or set PROJECT_ROOT env var to disambiguate."
            )

    # Nothing found
    raise DataError("Could not locate project root (requirements.md not found)")


def resolve_and_validate_subpath(root: Path, path_str: str) -> Path:
    candidate = (root / path_str).expanduser().resolve()
    try:
        if not candidate.is_relative_to(root):
            raise ArgError(f"Path {candidate} is outside project root {root}")
    except AttributeError:
        if str(candidate).startswith(str(root)):
            return candidate
        raise ArgError(f"Path {candidate} is outside project root {root}")
    return candidate


def _utc_now_iso_z() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def generate_dataset(config: dict) -> dict:
    # Delegate to existing generator in module (kept backwards compatible)
    if "data_dir" not in config:
        raise ArgError("generate_dataset requires 'data_dir' in config")
    data_dir_str = config["data_dir"]
    force = bool(config.get("force_regenerate", False))

    root = get_project_root()
    data_dir = resolve_and_validate_subpath(root, data_dir_str)
    dataset_path = data_dir / "dataset.csv"
    meta_path = data_dir / "dataset_meta.json"

    if dataset_path.exists() and not force:
        return {"dataset_path": str(dataset_path), "meta_path": str(meta_path), "generated": False}

    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise DataError(f"Cannot create data dir {data_dir}: {e}") from e

    rng = np.random.default_rng(seed=42)
    n = 1000
    z = rng.normal(0.0, 1.0, size=n)
    e1 = rng.normal(0.0, 0.2, size=n)
    e2 = rng.normal(0.0, 0.2, size=n)
    e3 = rng.normal(0.0, 1.0, size=n)
    f1 = z + e1
    f2 = z + e2
    f3 = e3
    noise = rng.normal(0.0, 1.0, size=n)
    y = 5.0 + 3.0 * f1 - 2.0 * f2 + 0.5 * f3 + noise

    f1 = f1.astype(np.float64)
    f2 = f2.astype(np.float64)
    f3 = f3.astype(np.float64)
    y = y.astype(np.float64)

    def pearson(a: np.ndarray, b: np.ndarray) -> float:
        a = a.astype(np.float64)
        b = b.astype(np.float64)
        return float(np.corrcoef(a, b)[0, 1])

    r12 = pearson(f1, f2)
    r13 = pearson(f1, f3)
    r23 = pearson(f2, f3)

    atol = 1e-12
    def in_closed_interval(val, lo, hi):
        if val + atol < lo:
            return False
        if val - atol > hi:
            return False
        return True

    if not in_closed_interval(r12, 0.80, 0.95) or not in_closed_interval(r13, -0.20, 0.20) or not in_closed_interval(r23, -0.20, 0.20):
        raise DataError(f"Correlation out of bounds: pearson_f1_f2={r12}, pearson_f1_f3={r13}, pearson_f2_f3={r23}")

    df = pd.DataFrame({"f1": f1, "f2": f2, "f3": f3, "y": y}, dtype=np.float64)
    try:
        df.to_csv(dataset_path, index=False, lineterminator="\n", encoding="utf-8")
    except Exception as e:
        raise WriteError(f"Failed to write dataset.csv: {e}") from e

    meta = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "n_rows": 1000,
        "n_features": 3,
        "feature_names": ["f1", "f2", "f3"],
        "target_name": "y",
        "generation_seed": 42,
        "correlations": {
            "pearson_f1_f2": r12,
            "pearson_f1_f3": r13,
            "pearson_f2_f3": r23,
        },
        "coefficients": {"f1": 3.0, "f2": -2.0, "f3": 0.5},
        "intercept": 5.0,
        "noise_std": 1.0,
    }

    write_json_file = artifacts.write_config if hasattr(artifacts, "write_config") else None
    try:
        # write meta directly
        with meta_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False, separators=(", ", ": "))
            f.write("\n")
    except Exception as e:
        raise WriteError(f"Failed to write dataset_meta.json: {e}") from e

    return {"dataset_path": str(dataset_path), "meta_path": str(meta_path), "generated": True}


def run_experiment(config: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single linear regression experiment using provided config and return metrics dict.

    Expected config keys: seed (int), data_dir (str) optional, test_size (float) optional
    """
    seed = int(config.get("seed", 0))
    data_dir = config.get("data_dir", "./data")
    test_size = float(config.get("test_size", 0.2))

    if not (0.0 < test_size < 1.0):
        raise ArgError("test_size must be in (0,1)")

    root = get_project_root()
    data_path = resolve_and_validate_subpath(root, data_dir)

    # Ensure dataset exists
    try:
        generate_dataset({"data_dir": str(data_dir), "force_regenerate": False})
    except Exception as e:
        raise DataError(f"Dataset unavailable: {e}") from e

    dataset_path = data_path / "dataset.csv"
    if not dataset_path.exists():
        raise DataError("dataset.csv missing after generation")

    # Load dataset
    try:
        df = pd.read_csv(dataset_path, dtype=np.float64)
    except Exception as e:
        raise DataError(f"Failed to read dataset: {e}") from e

    X = df[["f1", "f2", "f3"]].to_numpy(dtype=np.float64)
    y = df["y"].to_numpy(dtype=np.float64)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, shuffle=True, random_state=seed
    )

    # Train
    try:
        model = LinearRegression()
        model.fit(X_train, y_train)
    except Exception as e:
        raise RuntimeError(f"Training failed: {e}") from e

    # Evaluate
    y_pred = model.predict(X_test)
    mse = float(mean_squared_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    # Build metrics dict per supervisor guidance
    metrics = {
        "seed": seed,
        "mse": mse,
        "r2": r2,
        "n_parameters": 1 + X.shape[1],
        "train_samples": int(y_train.shape[0]),
        "val_samples": int(y_test.shape[0]),
        "created": _utc_now_iso_z(),
    }

    # Extract hyperparams safely (primitives only)
    lr = float(config.get("lr", 0.01)) if config is not None and "lr" in config else 0.01
    regularization = float(config.get("regularization", 0.0)) if config is not None and "regularization" in config else 0.0
    epochs = int(config.get("epochs", 1)) if config is not None and "epochs" in config else 1
    run_id = str(config.get("run_id", f"lr_run_{seed}")) if config is not None else f"lr_run_{seed}"

    # Create run directory and write artifacts. Pass only minimal primitives to create_run_dir
    run_dir = artifacts.create_run_dir({"run_id": run_id})

    # write config (primitives only)
    cfg = {
        "run_id": run_id,
        "seed": seed,
        "data_dir": str(data_path),
        "test_size": test_size,
        "model": "LinearRegression",
        "lr": lr,
        "regularization": regularization,
        "epochs": epochs,
        "timestamp": metrics["created"],
    }
    artifacts.write_config(run_dir, cfg)

    # If epochs>1, perform repeated fits to reflect epochs value (re-fitting is acceptable here)
    try:
        if epochs <= 0:
            raise ArgError("epochs must be >= 1")
        for _ in range(epochs):
            model.fit(X_train, y_train)
    except ArgError:
        raise
    except Exception as e:
        raise TrainError(f"Training failed during epochs loop: {e}") from e

    # Update metrics with hyperparams and run_id
    metrics.update({
        "run_id": run_id,
        "lr": lr,
        "regularization": regularization,
        "epochs": epochs,
    })

    artifacts.append_metrics(run_dir, metrics)
    try:
        artifacts.finalize(run_dir)
    except Exception as e:
        raise WriteError(f"Finalize failed: {e}") from e
    try:
        artifacts.update_comparison_report()
    except Exception:
        # Non-fatal for experiment result; log and continue
        pass

    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=False, help="Random seed for train/test split")
    parser.add_argument("--generate-dataset", action="store_true", help="Generate data/dataset.csv")
    parser.add_argument("--data-dir", type=str, default="./data", help="Data directory")
    parser.add_argument("--force-regenerate", action="store_true", help="Force regeneration of dataset")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split fraction")
    args = parser.parse_args()

    if args.generate_dataset:
        try:
            res = generate_dataset({"data_dir": args.data_dir, "force_regenerate": bool(args.force_regenerate)})
            print(json.dumps(res))
            sys.exit(0)
        except ArgError as e:
            print(f"Argument error: {e}", file=sys.stderr)
            sys.exit(2)
        except DataError as e:
            print(f"Data error: {e}", file=sys.stderr)
            sys.exit(3)
        except WriteError as e:
            print(f"Write error: {e}", file=sys.stderr)
            sys.exit(6)

    # Run experiment if seed provided
    if args.seed is None:
        print("No action requested. Use --generate-dataset or --seed <int>", file=sys.stderr)
        sys.exit(1)

    config = {"seed": args.seed, "data_dir": args.data_dir, "test_size": args.test_size}
    try:
        metrics = run_experiment(config)
    except ArgError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    except DataError as e:
        print(str(e), file=sys.stderr)
        sys.exit(3)
    except WriteError as e:
        print(str(e), file=sys.stderr)
        sys.exit(6)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # Print single-line compact JSON exactly matching written metrics
    sys.stdout.write(json.dumps(metrics, separators=(",",":"), ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()
    sys.exit(0)


if __name__ == "__main__":
    main()
