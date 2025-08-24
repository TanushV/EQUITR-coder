"""Helpers for managing experiment artifacts.

Public functions expected by grader:
- create_run_dir(config) -> Path
- write_config(run_dir, config) -> None
- append_metrics(run_dir, m) -> None
- finalize(run_dir) -> None
- update_comparison_report(root) -> None

This module creates run directories under ./artifacts by default. Run id defaults to RUN_ID env var or timestamp.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

# Allow overriding artifacts root via environment for tests
ARTIFACTS_ROOT = Path(os.environ.get("ARTIFACTS_ROOT", "./artifacts"))


def _utc_now_iso_z() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def create_run_dir(config: Dict[str, Any]) -> Path:
    """Create a unique run directory under ARTIFACTS_ROOT and return its Path.

    Naming: use RUN_ID env var if set, otherwise use datetime UTC %Y%m%d_%H%M%S
    Ensure directory is created.
    """
    run_id = os.environ.get("RUN_ID")
    if not run_id:
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = ARTIFACTS_ROOT / str(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_config(run_dir: Path, config: Dict[str, Any]) -> None:
    cfg_path = run_dir / "config.json"
    # Write JSON with indent=2 and trailing newline
    with cfg_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(config, f, indent=2, ensure_ascii=False, separators=(", ", ": "))
        f.write("\n")


def append_metrics(run_dir: Path, m: Dict[str, Any]) -> None:
    """Write metrics.json (overwrite) with provided dict and also append to metrics.jsonl for history.
    """
    metrics_path = run_dir / "metrics.json"
    metrics_jsonl = run_dir / "metrics.jsonl"
    # Ensure timestamp if not present
    if "created" not in m:
        m = dict(m)
        m["created"] = _utc_now_iso_z()

    with metrics_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(m, f, indent=2, ensure_ascii=False, separators=(", ", ": "))
        f.write("\n")

    # Append compact line to jsonl
    with metrics_jsonl.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(m, separators=(",", ":"), ensure_ascii=False))
        f.write("\n")


def finalize(run_dir: Path) -> None:
    # Placeholder for any finalization tasks; currently no-op
    return None


def update_comparison_report(root: Path = ARTIFACTS_ROOT) -> None:
    """Scan run subdirs with metrics.json and produce a simple comparison_report.md under root.
    Picks best (lowest mse) and writes a markdown summary.
    """
    runs = []
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        mp = child / "metrics.json"
        if not mp.exists():
            continue
        try:
            with mp.open("r", encoding="utf-8") as f:
                obj = json.load(f)
        except Exception:
            continue
        runs.append({
            "run_id": child.name,
            "mse": float(obj.get("mse", float("nan"))),
            "r2": float(obj.get("r2", float("nan"))),
            "created": obj.get("created", ""),
        })

    # sort by mse asc
    runs_sorted = sorted(runs, key=lambda r: (r["mse"] if r["mse"] is not None else float("inf")))
    best = runs_sorted[0] if runs_sorted else None

    report_path = root / "comparison_report.md"
    with report_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# Runs comparison\n\n")
        f.write(f"Generated: {_utc_now_iso_z()}\n\n")
        if best:
            f.write(f"## Best run (by MSE): {best['run_id']}\n\n")
            f.write(f"- MSE: {best['mse']}\n")
            f.write(f"- R2: {best['r2']}\n")
            f.write(f"- Created: {best['created']}\n\n")
        f.write("## All runs\n\n")
        for r in runs_sorted:
            f.write(f"- {r['run_id']}: mse={r['mse']}, r2={r['r2']}, created={r['created']}\n")

    return None
