"""Example: create a simple Mario-style platformer project using EQUITR Coder in multi-agent parallel mode with specialized agent profiles.

This script will:
1. Create an output directory `generated_projects/mario_game_<timestamp>`.
2. Enable verbose logging of every LLM exchange and tool invocation.
3. Launch `EquitrCoder` in multi-agent parallel mode with specialized agents using custom profiles.
4. Use specialized agent profiles: game_dev, level_designer, qa_engineer, devops, and audio_engineer.
5. Instruct the agents to implement a minimal Mario clone (Python + Pygame), tests and docs.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

from equitrcoder.core.unified_config import get_config
from equitrcoder.programmatic import EquitrCoder, MultiAgentTaskConfiguration

# Run with an activated virtual-env that has the required model keys exported.

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

TASK_NAME = "Mario-style platformer (Pygame)"
TASK_DESCRIPTION = (
    "Create a minimal but working side-scrolling Mario-style platformer using Python and Pygame. "
    "Include a player character that can move and jump, simple enemy, coins, scoring, collision detection, "
    "level data in JSON / CSV, and unit tests for core mechanics. Use simple colored rectangles for all "
    "game objects - no sprites or images needed. Provide README and usage instructions."
)

NUM_AGENTS = get_config('limits.max_workers', 5)
MAX_COST_USD = get_config('limits.max_cost', 30.0)  # Increased for multiple agents
SUPERVISOR_MODEL = get_config('orchestrator.supervisor_model', "gpt-5")
WORKER_MODEL = get_config('orchestrator.worker_model', "gpt-5-mini")

# Specialized team profiles for Mario game development
TEAM_PROFILES = [
    "game_dev",
    "level_designer",
    "qa_engineer",
    "devops",
    "audio_engineer",
]

# -----------------------------------------------------------------------------
# Helper: enable maximal logging (LLM responses + tool calls)
# -----------------------------------------------------------------------------

def configure_logging(log_dir: Path) -> None:
    """Configure rich logging; write everything to file and echo INFO to stdout."""
    log_dir.mkdir(parents=True, exist_ok=True)
    time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"run_{time_stamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )

    os.environ["EQUITR_DEBUG"] = "true"
    logging.getLogger(__name__).info("Logging initialised -> %s", log_file)


# -----------------------------------------------------------------------------
# Main async task
# -----------------------------------------------------------------------------

async def main() -> None:
    base_dir = Path("generated_projects")
    time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = base_dir / f"mario_game_{time_stamp}"
    project_dir.mkdir(parents=True, exist_ok=True)

    configure_logging(project_dir / "logs")

    coder = EquitrCoder(repo_path=str(project_dir), git_enabled=True, mode="multi")

    cfg = MultiAgentTaskConfiguration(
        description=TASK_NAME,
        max_workers=NUM_AGENTS,
        max_cost=MAX_COST_USD,
        max_iterations=get_config('limits.max_iterations', 50),
        supervisor_model=SUPERVISOR_MODEL,
        worker_model=WORKER_MODEL,
        auto_commit=True,
        team=TEAM_PROFILES,
    )

    logging.info("🚀 Starting multi-agent task with specialized team: %s", TEAM_PROFILES)
    logging.info("📋 Task name: %s", TASK_NAME)

    result = await coder.execute_task(
        task_description=TASK_DESCRIPTION,
        config=cfg,
    )

    if result.success:
        logging.info("✅ Project completed! Total cost: $%.2f", result.cost)
    else:
        logging.error("❌ Task failed: %s", result.error)


if __name__ == "__main__":
    asyncio.run(main()) 