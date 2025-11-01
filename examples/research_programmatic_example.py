import asyncio
import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path

from equitrcoder.programmatic.interface import EquitrCoder, ResearchTaskConfiguration

TASK_NAME = "Time series forecasting research (synthetic dataset)"
TASK_DESCRIPTION = "Use the provided synthetic time series dataset to plan, run, and report forecasting experiments."

LOG_BASENAME = "research_run.log"
SUMMARY_BASENAME = "research_run_summary.json"


def setup_logging(project_dir: Path) -> Path:
    """Configure console and file logging for this run and return the log file path."""
    log_path = project_dir / LOG_BASENAME
    # Ensure parent exists (should already exist, but be safe)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )
    return log_path


async def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = Path(f"generated_projects/research_{ts}").resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    log_path = setup_logging(project_dir)
    logging.info("Project directory: %s", project_dir)
    logging.info("All logs will be written to: %s", log_path)
    # Sandbox all commands and file ops to the project directory
    os.chdir(str(project_dir))

    # --- Prepare synthetic time-series data (single dataset only) ---
    data_dir = project_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Deterministic seed
    rng = random.Random(42)
    total_points = 1500
    seasonal_period = 24
    trend_coef = 0.002
    ar1, ar2 = 0.5, -0.15
    noise_std = 0.6

    dataset_path = data_dir / "synthetic_timeseries.csv"
    with dataset_path.open("w", encoding="utf-8") as f:
        f.write("t,y\n")
        y1 = 0.0
        y2 = 0.0
        import math

        for t in range(total_points):
            trend = trend_coef * t
            season = 1.4 * math.sin(2 * math.pi * t / seasonal_period)
            ar = ar1 * y1 + ar2 * y2
            noise = rng.gauss(0.0, noise_std)
            y = trend + season + ar + noise
            f.write(f"{t},{y:.6f}\n")
            y2, y1 = y1, y

    logging.info(
        "Dataset generated at %s with %d points (seasonal_period=%d, trend_coef=%.4f, ar=(%.2f, %.2f), noise_std=%.2f)",
        dataset_path,
        total_points,
        seasonal_period,
        trend_coef,
        ar1,
        ar2,
        noise_std,
    )

    # No explicit experiments; only dataset is provided for the agent

    # --- Configure research task ---
    coder = EquitrCoder(repo_path=str(project_dir), mode="research")
    config = ResearchTaskConfiguration(
        description=TASK_NAME,
        max_workers=3,
        max_cost=12.0,
        supervisor_model="gpt-5",
        worker_model="gpt-5-mini",
        team=["ml_researcher", "data_engineer", "experiment_runner"],
        research_context={
            "datasets": [
                {
                    "path": str(dataset_path),
                    "description": "Synthetic univariate time series (trend+seasonality+AR+noise)",
                }
            ],
            # Provide simple, cross-platform experiments that always pass
            "experiments": [
                {
                    "name": "smoke",
                    "command": "python -c \"print('ok')\"",
                    "timeout": 120,
                }
            ],
        },
    )
    logging.info("Starting research task: %s", TASK_NAME)
    logging.info(
        "Config: max_workers=%d, max_cost=%.2f, supervisor_model=%s, worker_model=%s, team=%s",
        config.max_workers,
        config.max_cost,
        config.supervisor_model,
        config.worker_model,
        ",".join(config.team),
    )
    result = await coder.execute_task(TASK_DESCRIPTION, config)
    print("Success:", result.success)
    print("Cost:", result.cost)
    print("Execution Time:", result.execution_time)
    if result.error:
        print("Error:", result.error)
    logging.info(
        "Task finished. Success=%s, Cost=%.4f, Execution Time=%.2fs",
        result.success,
        result.cost,
        result.execution_time,
    )
    if result.error:
        logging.error("Error: %s", result.error)

    # Persist a machine-readable summary at the end
    summary = {
        "task_name": TASK_NAME,
        "task_description": TASK_DESCRIPTION,
        "timestamp_iso": datetime.now().isoformat(),
        "project_dir": str(project_dir),
        "dataset_path": str(dataset_path),
        "config": {
            "max_workers": 3,
            "max_cost": 12.0,
            "supervisor_model": "gpt-4o-mini",
            "worker_model": "gpt-4o-mini",
            "team": ["ml_researcher", "data_engineer", "experiment_runner"],
            "experiments": [
                {
                    "name": "smoke",
                    "command": "python -c \"print('ok')\"",
                    "timeout": 120,
                }
            ],
        },
        "result": {
            "success": bool(getattr(result, "success", False)),
            "cost": float(getattr(result, "cost", 0.0)),
            "execution_time": float(getattr(result, "execution_time", 0.0)),
            "error": getattr(result, "error", None),
        },
        "log_file": str(log_path),
    }
    summary_path = project_dir / SUMMARY_BASENAME
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logging.info("Summary written to: %s", summary_path)
    logging.info("Full logs available at: %s", log_path)
    print("\nSaved:")
    print(" - Log:", log_path)
    print(" - Summary:", summary_path)


if __name__ == "__main__":
    asyncio.run(main())
