import asyncio
from equitrcoder.programmatic.interface import EquitrCoder, ResearchTaskConfiguration


TASK_NAME = "CIFAR-10 ResNet ablation"
TASK_DESCRIPTION = (
    "Evaluate a ResNet classifier on CIFAR-10 with two training runs: "
    "(1) baseline; (2) data augmentation enabled."
)


async def main():
    coder = EquitrCoder(repo_path=".", mode="research")
    config = ResearchTaskConfiguration(
        description=TASK_NAME,
        max_workers=3,
        max_cost=12.0,
        supervisor_model="gpt-5",
        worker_model="gpt-5-mini",
        team=["ml_researcher", "data_engineer", "experiment_runner"],
        research_context={
            "datasets": [
                {"path": "./data/cifar10", "description": "Local CIFAR-10 dataset folder"}
            ],
            "experiments": [
                {"name": "baseline", "command": "python train.py --dataset cifar10 --epochs 1"},
                {"name": "augmented", "command": "python train.py --dataset cifar10 --epochs 1 --augment"},
            ],
        },
    )
    result = await coder.execute_task(TASK_DESCRIPTION, config)
    print("Success:", result.success)
    print("Cost:", result.cost)
    print("Execution Time:", result.execution_time)


if __name__ == "__main__":
    asyncio.run(main()) 