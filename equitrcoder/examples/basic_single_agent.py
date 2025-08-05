#!/usr/bin/env python3
"""
Basic Single-Agent Example (v2)

Demonstrates the modern programmatic interface to EQUITR Coder after the v2.1 refactor.
Run this script from the project root in an environment that has the required LLM
keys set (e.g. ``OPENAI_API_KEY`` or ``MOONSHOT_API_KEY``).

The script will:
1. Create ``generated_projects/single_agent_demo`` (if it does not exist).
2. Instantiate an ``EquitrCoder`` instance pointed at that directory.
3. Execute a simple analysis task with sensible cost/iteration limits.
4. Print the result summary.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from equitrcoder.programmatic import EquitrCoder, TaskConfiguration


async def main() -> None:
    print("🚀 equitrcoder Single-Agent Example (v2)")

    # Basic sanity check for API keys
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("MOONSHOT_API_KEY")):
        print("⚠️  No LLM API key found – set OPENAI_API_KEY or MOONSHOT_API_KEY first.")
        return

    project_dir = Path("generated_projects/single_agent_demo")
    project_dir.mkdir(parents=True, exist_ok=True)

    coder = EquitrCoder(repo_path=str(project_dir), git_enabled=True)

    config = TaskConfiguration(
        description="Analyze the current repository structure and suggest improvements.",
        max_cost=2.0,
        max_iterations=15,
        model="gpt-4o-mini",
        auto_commit=True,
    )

    result = await coder.execute_task(task_description=config.description, config=config)

    if result.success:
        print(f"✅ Task completed – total cost: ${result.cost:.2f}")
    else:
        print(f"❌ Task failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
