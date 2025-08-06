"""Example: create a simple Mario-style platformer project using EQUITR Coder in multi-agent parallel mode with specialized agent profiles.

This script will:
1. Create an output directory `generated_projects/mario_game_<timestamp>`.
2. Enable verbose logging of every LLM exchange and tool invocation.
3. Launch `EquitrCoder` in multi-agent parallel mode with 5 specialized agents using custom profiles.
4. Use specialized agent profiles: game_dev, level_designer, qa_engineer, devops, and audio_engineer.
5. Instruct the agents to implement a minimal Mario clone (Python + Pygame), tests and docs.

The agents will use their specialized profiles to:
- game_dev: Handle core game mechanics, physics, and engine systems
- level_designer: Create level data, game balance, and content
- qa_engineer: Implement testing frameworks and quality assurance
- devops: Set up project structure, CI/CD, and build systems

Run with an activated virtual-env that has the required model keys exported.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

from equitrcoder.programmatic import EquitrCoder, MultiAgentTaskConfiguration

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

NUM_AGENTS = 5
MAX_COST_USD = 30.0  # Increased for 5 agents
SUPERVISOR_MODEL = "o3"  # Using O3 for supervisor (orchestrator and audit)
WORKER_MODEL = "gpt-4.1"  # Using working DeepSeek model for workers

# Specialized team profiles for Mario game development
TEAM_PROFILES = [
    "game_dev",        # Core game mechanics, physics, collision detection
    "level_designer",  # Level data, game balance, content creation
    "qa_engineer",     # Testing frameworks, quality assurance
    "devops",          # Project setup, CI/CD, build systems
    "audio_engineer"   # Audio systems, sound effects, music integration
]

TASK_DESCRIPTION = (
    "Create a minimal but working side-scrolling Mario-style platformer using Python and Pygame. "
    "Include a player sprite that can move and jump, simple enemy, coins, scoring, collision detection,"
    " level data in JSON / CSV, and unit tests for core mechanics. Provide README and usage instructions."
)

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

    # Optional: instruct EQUITR Coder internals to be verbose
    os.environ["EQUITR_DEBUG"] = "true"
    logging.getLogger(__name__).info("Logging initialised -> %s", log_file)


# -----------------------------------------------------------------------------
# Main async task
# -----------------------------------------------------------------------------

async def main() -> None:
    # 1. Create project directory
    base_dir = Path("generated_projects")
    time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = base_dir / f"mario_game_{time_stamp}"
    project_dir.mkdir(parents=True, exist_ok=True)

    # 2. Configure logging into the project folder
    configure_logging(project_dir / "logs")

    # 3. Instantiate coder
    coder = EquitrCoder(repo_path=str(project_dir), git_enabled=True)

    cfg = MultiAgentTaskConfiguration(
        description=TASK_DESCRIPTION,
        num_agents=NUM_AGENTS,
        max_cost=MAX_COST_USD,
        max_iterations=50,
        supervisor_model=SUPERVISOR_MODEL,
        worker_model=WORKER_MODEL,
        auto_commit=True,
        team=TEAM_PROFILES  # Pass the specialized team profiles
    )

    logging.info("🚀 Starting multi-agent task with specialized team: %s", TEAM_PROFILES)
    logging.info("📋 Task description: %s", TASK_DESCRIPTION)
    
    # Execute task with specialized team profiles
    result = await coder.execute_task(
        task_description=TASK_DESCRIPTION, 
        config=cfg
    )

    if result.success:
        logging.info("✅ Project completed! Total cost: $%.2f", result.cost)
    else:
        logging.error("❌ Task failed: %s", result.error)


if __name__ == "__main__":
    asyncio.run(main()) 