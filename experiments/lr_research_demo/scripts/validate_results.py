#!/usr/bin/env python3
"""Validate experiment runs against thresholds and produce a report.

Usage: python scripts/validate_results.py --task-dir docs/task_20250824_014708

Writes:
 - {task_dir}/validation_report.json
 - {task_dir}/validation_status.txt

Behavior:
 - Reads runs_summary.csv produced by exec_experiments.py
 - Reads experiments.yaml for optional per-experiment validation overrides
 - Default thresholds: max_mse=2.0, min_r2=0.60
 - pass if (mse <= max_mse) and (r2 >= min_r2)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd

try:
    import yaml
except Exception as exc:  # pragma: no cover - yaml must be installed in environment
    raise SystemExit("PyYAML is required: please install pyyaml") from exc


DEFAULT_MAX_MSE = 2.0
DEFAULT_MIN_R2 = 0.60


def load_experiments_yaml(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    experiments = data.get("experiments", []) if isinstance(data, dict) else []
    by_name: Dict[str, Dict[str, Any]] = {}
    for e in experiments:
        name = e.get("name")
        if name:
            by_name[name] = e
    return by_name


def evaluate_row(row: pd.Series, experiments_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    name = row.get("name") or row.get("run_id")
    seed = int(row.get("seed")) if not pd.isna(row.get("seed")) else None
    mse = None if pd.isna(row.get("mse")) else float(row.get("mse"))
    r2 = None if pd.isna(row.get("r2")) else float(row.get("r2"))

    # Look up experiment by name
    exp = experiments_map.get(name, {}) if name else {}
    validation = exp.get("validation", {}) if isinstance(exp, dict) else {}

    max_mse = float(validation.get("max_mse", DEFAULT_MAX_MSE))
    min_r2 = float(validation.get("min_r2", DEFAULT_MIN_R2))

    reasons = []
    passed = True
    if mse is None:
        passed = False
        reasons.append("mse:missing")
    else:
        if not (mse <= max_mse):
            passed = False
            reasons.append("mse>threshold")
    if r2 is None:
        passed = False
        reasons.append("r2:missing")
    else:
        if not (r2 >= min_r2):
            passed = False
            reasons.append("r2<threshold")

    out = {
        "run_id": row.get("run_id") if not pd.isna(row.get("run_id")) else name,
        "name": name,
        "seed": seed,
        "mse": mse,
        "r2": r2,
        "mse_threshold": max_mse,
        "r2_threshold": min_r2,
        "pass": bool(passed),
        "reasons": reasons,
    }
    return out


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--task-dir", type=str, default="docs/task_20250824_014708")
    args = p.parse_args(argv)

    task_dir = Path(args.task_dir)
    if not task_dir.exists():
        raise SystemExit(f"Task dir not found: {task_dir}")

    runs_csv = task_dir / "runs_summary.csv"
    if not runs_csv.exists():
        raise SystemExit(f"runs_summary.csv not found in {task_dir}")

    df = pd.read_csv(runs_csv)

    experiments_yaml = task_dir / "experiments.yaml"
    experiments_map = load_experiments_yaml(experiments_yaml)

    results = []
    for _, row in df.iterrows():
        res = evaluate_row(row, experiments_map)
        results.append(res)

    overall_pass = all(r.get("pass", False) for r in results)

    report = {"runs": results, "overall_pass": bool(overall_pass)}

    # Write JSON report with indent=2 and trailing newline
    report_path = task_dir / "validation_report.json"
    with report_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, separators=(", ", ": "))
        f.write("\n")

    status_path = task_dir / "validation_status.txt"
    status_text = "PASS" if overall_pass else "FAIL"
    status_path.write_text(status_text + "\n", encoding="utf-8", newline="\n")

    print(f"Wrote {report_path} and {status_path}")


if __name__ == "__main__":
    main()
