import asyncio
from pathlib import Path
from equitrcoder.programmatic.interface import EquitrCoder, ResearchTaskConfiguration


def main():
    project_dir = Path(__file__).parent.resolve()

    # Description: complete two linear regression experiments on a synthetic correlated dataset
    task_description = (
        "Finish a small ML project to run two linear regression experiments on a simple, correlated,"
        " randomly generated dataset. Ensure training, evaluation (MSE/R2), and comparison of the two runs."
        " Keep all work inside this folder only."
    )

    # Provide a basic research context to avoid interactive prompts
    research_context = {
        "datasets": [
            {"path": str(project_dir / "data"), "description": "Synthetic data folder (to be generated)"}
        ],
        "hardware": {"note": "Local CPU preferred"},
        "experiments": [
            {"name": "lr_run_1", "command": "python -m experiments.lr_research_demo.scripts.run_lr --seed 1", "cwd": str(Path.cwd())},
            {"name": "lr_run_2", "command": "python -m experiments.lr_research_demo.scripts.run_lr --seed 2", "cwd": str(Path.cwd())},
        ],
    }

    async def run():
        coder = EquitrCoder(repo_path=str(project_dir), git_enabled=True, mode="research", max_workers=3)
        config = ResearchTaskConfiguration(
            description=task_description,
            max_workers=3,
            max_cost=6.0,
            max_iterations=60,
            supervisor_model=None,
            worker_model=None,
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