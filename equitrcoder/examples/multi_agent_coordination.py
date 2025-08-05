#!/usr/bin/env python3
"""
Multi-Agent Coordination Example (v2)

Uses the modern ``EquitrCoder`` programmatic interface introduced in v2.1 to run a
parallel task with multiple agents. Older orchestrator/worker abstractions were
removed from the library, so those imports have been replaced.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path

from equitrcoder.programmatic import EquitrCoder, MultiAgentTaskConfiguration


async def main() -> None:
    print("🚀 equitrcoder Multi-Agent Coordination Example (v2)")

    if not (os.getenv("OPENAI_API_KEY") or os.getenv("MOONSHOT_API_KEY")):
        print("⚠️  No LLM API key found – set OPENAI_API_KEY or MOONSHOT_API_KEY first.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = Path(f"generated_projects/multi_agent_demo_{timestamp}")
    project_dir.mkdir(parents=True, exist_ok=True)

    coder = EquitrCoder(repo_path=str(project_dir), git_enabled=True)

    cfg = MultiAgentTaskConfiguration(
        description=(
            "Perform a parallel analysis of the core and UI modules, then generate a "
            "comprehensive architecture report with recommendations."
        ),
        num_agents=3,
        supervisor_model="gpt-4o-mini",
        worker_model="gpt-4o-mini",
        max_cost=5.0,
        auto_commit=True,
    )

    result = await coder.execute_task(task_description=cfg.description, config=cfg)

    if result.success:
        print(f"✅ Multi-agent task completed – total cost: ${result.cost:.2f}")
    else:
        print(f"❌ Task failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
