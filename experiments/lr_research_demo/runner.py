#!/usr/bin/env python3
"""CLI runner wrapper: provides subcommands run, list, show.

- runner.py run --seed <int> [--data-dir ./data] [--outdir ./artifacts]
- runner.py list [--json] [--outdir ./artifacts]
- runner.py show <run_id> [--outdir ./artifacts]

Preserve original EquitrCoder demo if environment variable EQUITR is set.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Keep legacy EquitrCoder demo behind env guard
if os.environ.get("EQUITR"):
    import asyncio
    from pathlib import Path as _Path
    from equitrcoder.programmatic.interface import EquitrCoder, ResearchTaskConfiguration

    def main():
        project_dir = _Path(__file__).parent.resolve()
        task_description = (
            "Finish a small ML project to run two linear regression experiments on a simple, correlated,"
            " randomly generated dataset. Ensure training, evaluation (MSE/R2), and comparison of the two runs."
            " Keep all work inside this folder only."
        )

        research_context = {
            "datasets": [
                {"path": str(project_dir / "data"), "description": "Synthetic data folder (to be generated)"}
            ],
            "hardware": {"note": "Local CPU preferred"},
            "experiments": [
                {"name": "lr_run_1", "command": "python scripts/run_lr.py --seed 1", "cwd": "."},
                {"name": "lr_run_2", "command": "python scripts/run_lr.py --seed 2", "cwd": "."},
            ],
        }

        async def run():
            coder = EquitrCoder(repo_path=str(project_dir), git_enabled=True, mode="research", max_workers=3)
            config = ResearchTaskConfiguration(
                description=task_description,
                max_workers=3,
                max_cost=6.0,
                max_iterations=60,
                supervisor_model="gpt-5",
                worker_model="gpt-5-mini",
                auto_commit=True,
                team=["ml_researcher", "data_engineer", "experiment_runner"],
                research_context=research_context,
            )
            result = await coder.execute_task(task_description, config)
            print("Success:", result.success)
            if result.error:
                print("Error:", result.error)
            print("Cost:", result.cost)
            print("Iterations:", result.iterations)

        asyncio.run(run())

    if __name__ == "__main__":
        main()
    sys.exit(0)

# New CLI implementation
ARTIFACTS_ROOT = Path("./artifacts")


def list_runs(outdir: Path, as_json: bool = False):
    runs = []
    if outdir.exists():
        for child in sorted(outdir.iterdir()):
            if not child.is_dir():
                continue
            mp = child / "metrics.json"
            if not mp.exists():
                continue
            try:
                with mp.open("r", encoding="utf-8") as f:
                    m = json.load(f)
            except Exception:
                continue
            runs.append({
                "run_id": child.name,
                "mse": m.get("mse"),
                "r2": m.get("r2"),
                "created": m.get("created"),
            })
    if as_json:
        print(json.dumps(runs, ensure_ascii=False))
    else:
        # simple table
        print("run_id\tmse\tr2\tcreated")
        for r in runs:
            print(f"{r['run_id']}\t{r['mse']}\t{r['r2']}\t{r['created']}")


def show_run(outdir: Path, run_id: str):
    run_dir = outdir / run_id
    if not run_dir.exists():
        print(f"Run {run_id} not found", file=sys.stderr)
        sys.exit(2)
    cfgp = run_dir / "config.json"
    mp = run_dir / "metrics.json"
    if cfgp.exists():
        with cfgp.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = None
    if mp.exists():
        with mp.open("r", encoding="utf-8") as f:
            m = json.load(f)
    else:
        m = None
    out = {"run_id": run_id, "config": cfg, "metrics": m}
    print(json.dumps(out, indent=2, ensure_ascii=False))


def run_command(args: argparse.Namespace):
    # Delegate to scripts.run_lr
    import importlib
    try:
        mod = importlib.import_module("scripts.run_lr")
    except Exception as e:
        print(f"Failed to import scripts.run_lr: {e}", file=sys.stderr)
        sys.exit(1)

    cfg = {"seed": args.seed, "data_dir": args.data_dir, "test_size": args.test_size}
    try:
        metrics = mod.run_experiment(cfg)
    except Exception as e:
        print(f"Experiment failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Print compact single-line JSON (mod.run_experiment returns dict)
    print(json.dumps(metrics, separators=(",", ":"), ensure_ascii=False))


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="runner.py")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run")
    p_run.add_argument("--seed", type=int, required=True)
    p_run.add_argument("--data-dir", type=str, default="./data")
    p_run.add_argument("--test-size", type=float, default=0.2)

    p_list = sub.add_parser("list")
    p_list.add_argument("--json", action="store_true")
    p_list.add_argument("--outdir", type=str, default=str(ARTIFACTS_ROOT))

    p_show = sub.add_parser("show")
    # positional arguments must not use 'required'
    p_show.add_argument("run_id", type=str)
    p_show.add_argument("--outdir", type=str, default=str(ARTIFACTS_ROOT))

    return parser.parse_args(argv)


def main(argv: Optional[list] = None):
    args = parse_args(argv)
    if args.cmd == "list":
        list_runs(Path(args.outdir), as_json=getattr(args, "json", False))
    elif args.cmd == "show":
        show_run(Path(args.outdir), args.run_id)
    elif args.cmd == "run":
        run_command(args)
    else:
        print("No command specified. Use run|list|show", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
