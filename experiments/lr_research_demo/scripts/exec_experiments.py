#!/usr/bin/env python3
"""Execute experiments listed in a task experiments.yaml and collect outputs.

Usage:
  python scripts/exec_experiments.py --task-dir docs/task_20250824_014708

This script will:
 - Read experiments.yaml under the provided task dir
 - For each experiment entry, invoke: python runner.py run --seed <seed> --data-dir <data_dir> --test-size <test_size>
 - Capture stdout (metrics JSON) to docs/.../runs/<run_id>.json
 - Capture combined stdout+stderr to docs/.../logs/<run_id>.log
 - Append a row to runs_summary.csv with required columns
 - Write metadata.json for the batch

"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except Exception:
    yaml = None


def _utc_now_compact() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def load_experiments_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    txt = path.read_text(encoding="utf-8")
    if yaml is None:
        # Try a very small fallback for the expected structure by replacing ':' with '': not robust.
        raise RuntimeError("PyYAML is required to parse experiments.yaml. Please install pyyaml.")
    return yaml.safe_load(txt)


def run_one(experiment: Dict[str, Any], idx: int, task_dir: Path, artifacts_root: Path) -> Dict[str, Any]:
    # Determine run_id
    env_run_id = os.environ.get("RUN_ID")
    if env_run_id:
        run_id = env_run_id
    else:
        run_id = f"{idx}_{_utc_now_compact()}"

    runs_dir = task_dir / "runs"
    logs_dir = task_dir / "logs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    seed = int(experiment.get("seed", 0))
    data_dir = str(experiment.get("data_dir", "./data"))
    test_size = float(experiment.get("test_size", 0.2))

    cmd = [sys.executable, "runner.py", "run", "--seed", str(seed), "--data-dir", data_dir, "--test-size", str(test_size)]

    proc = subprocess.run(cmd, capture_output=True, text=True)

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    # Write stdout JSON to runs/<run_id>.json
    run_json_path = runs_dir / f"{run_id}.json"
    run_log_path = logs_dir / f"{run_id}.log"

    run_json_path.write_text(stdout, encoding="utf-8")

    # Write combined log
    with run_log_path.open("w", encoding="utf-8", newline="\n") as f:
        if stdout:
            f.write("STDOUT:\n")
            f.write(stdout)
            if not stdout.endswith("\n"):
                f.write("\n")
        if stderr:
            f.write("STDERR:\n")
            f.write(stderr)
            if not stderr.endswith("\n"):
                f.write("\n")

    # Parse metrics from stdout
    try:
        metrics = json.loads(stdout) if stdout.strip() else {}
    except Exception:
        metrics = {}

    # Prepare summary row
    summary = {
        "run_id": run_id,
        "seed": seed,
        "mse": metrics.get("mse"),
        "r2": metrics.get("r2"),
        "train_samples": metrics.get("train_samples"),
        "val_samples": metrics.get("val_samples"),
        "created": metrics.get("created"),
    }
    # Include extra hyperparams
    for k, v in experiment.items():
        if k not in summary:
            summary[k] = v

    # Also include exit code
    summary["exit_code"] = int(proc.returncode)
    summary["artifacts_root"] = str(artifacts_root.resolve())

    return summary


def write_runs_summary(summaries: list[Dict[str, Any]], out_csv: Path) -> None:
    if not summaries:
        return
    # Collect all keys to include in CSV header
    keys = [
        "run_id",
        "seed",
        "mse",
        "r2",
        "train_samples",
        "val_samples",
        "created",
    ]
    extra_keys = []
    for s in summaries:
        for k in s.keys():
            if k not in keys and k not in extra_keys:
                extra_keys.append(k)
    header = keys + extra_keys
    with out_csv.open("w", encoding="utf-8", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for s in summaries:
            writer.writerow(s)


def write_metadata(task_dir: Path, artifacts_root: Path, start_ts: str, end_ts: str, experiments_count: int) -> None:
    meta = {
        "task_dir": str(task_dir.resolve()),
        "artifacts_root": str(artifacts_root.resolve()),
        "start_utc": start_ts,
        "end_utc": end_ts,
        "n_experiments": experiments_count,
        "user": os.environ.get("USER") or os.environ.get("USERNAME"),
    }
    # Try to include git commit if available
    try:
        import subprocess as _sub
        out = _sub.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        meta["git_commit"] = out
    except Exception:
        meta["git_commit"] = None

    (task_dir / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--task-dir", type=str, default="docs/task_20250824_014708")
    args = p.parse_args(argv)

    task_dir = Path(args.task_dir)
    task_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = task_dir / "experiments.yaml"
    data = load_experiments_yaml(yaml_path)
    experiments = data.get("experiments", []) if isinstance(data, dict) else []

    artifacts_root = Path("./artifacts")

    start_ts = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    summaries = []
    for idx, exp in enumerate(experiments, start=1):
        s = run_one(exp, idx, task_dir, artifacts_root)
        summaries.append(s)

    end_ts = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

    # write runs_summary.csv
    write_runs_summary(summaries, task_dir / "runs_summary.csv")

    write_metadata(task_dir, artifacts_root, start_ts, end_ts, len(experiments))

    # Exit status: 0 even if some runs failed; validation script can be run separately
    print(f"Executed {len(experiments)} experiments, outputs in {task_dir}")


if __name__ == "__main__":
    main()
