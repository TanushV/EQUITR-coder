#!/usr/bin/env python3
"""
React Dog Hat Store (Minimal Example)

This example uses EQUITR Coder to scaffold a simple React website with a few
interactive features. It demonstrates the standardized pattern:
- Short task name in config.description
- Detailed task body passed to execute_task
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime

from equitrcoder.programmatic import EquitrCoder, TaskConfiguration
from equitrcoder.core.unified_config import get_config

TASK_NAME = "Dog Hat Store (React)"

TASK_DESCRIPTION = """
Create a simple React app (React 18+ with Vite) for a playful dog hat store.

Requirements:
- Pages: Home, Catalog, Product, About
- Features: product listing, size selection, basic cart add/remove
- Styling: modern, responsive, lightweight
- Dev setup: npm install, dev server, README with run instructions
- Data: sample products (JSON)
- Tests: basic component test(s)
"""


async def main() -> None:
    # Ensure API key(s) exist
    if not (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("MOONSHOT_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
    ):
        print(
            "⚠️  No API keys found. Set OPENAI_API_KEY, MOONSHOT_API_KEY, or ANTHROPIC_API_KEY."
        )
        return

    # Project directory (unique per run)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = Path(f"generated_projects/dog_hat_store_{ts}").resolve()
    # Ensure all file ops happen inside project folder
    project_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(str(project_dir))

    # Create coder
    coder = EquitrCoder(repo_path=str(project_dir), git_enabled=True)

    # Short task name in config; long body via execute_task
    config = TaskConfiguration(
        description=TASK_NAME,
        max_cost=get_config("limits.max_cost", 8.0),
        max_iterations=get_config("limits.max_iterations", 40),
        model=get_config("llm.model", "gpt-5-mini"),
        auto_commit=True,
    )

    print("🚀 Creating React dog hat store...")
    result = await coder.execute_task(TASK_DESCRIPTION, config=config)

    if result.success:
        print("✅ Success")
        print(f"📍 Project: {project_dir}")
        print(f"💰 Cost: ${result.cost:.4f} | ⏱ {result.execution_time:.1f}s")
    else:
        print("❌ Failed:", result.error)

    await coder.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
