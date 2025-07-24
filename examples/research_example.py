#!/usr/bin/env python3
"""
Example usage of ResearchOrchestrator for ML research workflows.

This example demonstrates:
1. Creating a research orchestrator with machine-aware scaling
2. Setting up experiment configurations
3. Running experiments with parallel workers
4. Coordinating multi-iteration research workflows
"""

import asyncio
import sys
from pathlib import Path

from equitrcoder import (
    create_research_orchestrator,
    ExperimentConfig,
    WorkerConfig,
)

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


async def simple_experiment_example():
    """Example of running a simple experiment with machine-aware scaling."""
    print("=== Simple Experiment Example ===")

    # Create research orchestrator with custom settings
    orchestrator = create_research_orchestrator(
        scale_factor=0.8,  # Scale down for this example
        experiments_dir="./example_experiments",
        global_cost_limit=5.0,  # Lower cost limit for example
    )

    # Detect machine specifications
    machine_specs = orchestrator._detect_machine_specs()
    cpu_cores = machine_specs.cpu_cores
    ram_gb = machine_specs.ram_gb
    print(f"Detected machine: {cpu_cores} cores, {ram_gb:.1f}GB RAM")

    # Create experiment configuration
    config = ExperimentConfig(
        experiment_id="simple_mnist_001",
        name="Simple MNIST Classification",
        description="Train a simple neural network on MNIST dataset",
        hyperparameters={
            "batch_size": 128,
            "epochs": 5,
            "learning_rate": 0.001,
            "hidden_size": 256,
            "dropout": 0.2,
        },
        environment_requirements=["torch", "torchvision", "numpy"],
        expected_duration_mins=10,
    )

    print(f"Created experiment: {config.name}")
    print(f"Base hyperparameters: {config.hyperparameters}")

    # Scale the parameters for the current machine
    scaled_params = orchestrator._scale_experiment_params(
        config.hyperparameters, machine_specs
    )
    print(f"Scaled hyperparameters: {scaled_params}")

    # Generate experiment documentation
    try:
        docs = await orchestrator.generate_experiment_docs(config)
        print(f"Documentation generation success: {docs['generation_success']}")
        if docs["errors"]:
            print(f"Documentation errors: {docs['errors']}")
    except Exception as e:
        print(f"Documentation generation failed: {e}")

    # In a real scenario, you would run the experiment:
    # result = await orchestrator.run_experiment(config)
    # print(f"Experiment success: {result.success}")

    print("Simple experiment example completed!\n")


async def research_workflow_example():
    """Example of a complete research workflow with iterations."""
    print("=== Research Workflow Example ===")

    # Create research orchestrator
    create_research_orchestrator(
        scale_factor=1.0,
        experiments_dir="./research_experiments",
        max_concurrent_workers=2,
        global_cost_limit=10.0,
    )

    # Research question
    research_question = (
        "What is the optimal architecture for classifying handwritten digits?"
    )

    # Initial experiment configuration
    initial_config = ExperimentConfig(
        experiment_id="research_001",
        name="Architecture Comparison Study",
        description=(
            "Compare different neural network architectures for digit classification"
        ),
        hyperparameters={
            "batch_size": 64,
            "epochs": 3,  # Short for example
            "learning_rate": 0.001,
        },
    )

    print(f"Research question: {research_question}")
    print(f"Initial experiment: {initial_config.name}")

    # In a real scenario, you would run the full workflow:
    # workflow_result = await orchestrator.coordinate_research_workflow(
    #     research_question=research_question,
    #     initial_config=initial_config,
    #     max_iterations=3,
    # )
    #
    # print(f"Research workflow completed!")
    # print(f"Total experiments: {workflow_result['total_experiments']}")
    # print(f"Successful experiments: {workflow_result['successful_experiments']}")
    # print(f"Total cost: ${workflow_result['total_cost']:.4f}")

    print("Research workflow example completed!\n")


async def parallel_workers_example():
    """Example of using parallel workers for sub-tasks."""
    print("=== Parallel Workers Example ===")

    orchestrator = create_research_orchestrator()

    # Create worker configurations for different tasks
    worker_configs = [
        WorkerConfig(
            worker_id="data_worker",
            scope_paths=["./data", "./experiments"],
            allowed_tools=["read_file", "edit_file", "run_cmd"],
            max_cost=1.0,
            max_iterations=10,
        ),
        WorkerConfig(
            worker_id="model_worker",
            scope_paths=["./models", "./experiments"],
            allowed_tools=["read_file", "edit_file", "run_cmd"],
            max_cost=2.0,
            max_iterations=20,
        ),
        WorkerConfig(
            worker_id="eval_worker",
            scope_paths=["./experiments", "./results"],
            allowed_tools=["read_file", "run_cmd"],
            max_cost=0.5,
            max_iterations=5,
        ),
    ]

    # Create workers
    workers = []
    for config in worker_configs:
        worker = orchestrator.create_worker(config)
        workers.append(worker)
        print(f"Created worker: {config.worker_id}")

    # Define parallel tasks
    tasks = [
        {
            "task_id": "data_preprocessing",
            "worker_id": "data_worker",
            "task_description": "Preprocess and validate dataset for ML experiment",
        },
        {
            "task_id": "model_setup",
            "worker_id": "model_worker",
            "task_description": "Set up and configure ML model architecture",
        },
        {
            "task_id": "evaluation_prep",
            "worker_id": "eval_worker",
            "task_description": "Prepare evaluation metrics and visualization tools",
        },
    ]

    print(f"Prepared {len(tasks)} parallel tasks")

    # In a real scenario, you would execute the tasks:
    # results = await orchestrator.execute_parallel_tasks(tasks)
    #
    # for result in results:
    #     print(f"Task {result.task_id}: {'Success' if result.success else 'Failed'}")
    #     if not result.success:
    #         print(f"  Error: {result.error}")

    print("Parallel workers example completed!\n")


def callbacks_example():
    """Example of setting up callbacks for monitoring."""
    print("=== Callbacks Example ===")

    def on_experiment_start(config):
        print(f"🚀 Starting experiment: {config.name}")

    def on_experiment_complete(result):
        status = "✅ Success" if result.success else "❌ Failed"
        exp_id = result.experiment_id
        exec_time = result.execution_time
        print(f"{status} Experiment {exp_id} completed in {exec_time:.2f}s")
        if result.error:
            print(f"   Error: {result.error}")

    def on_machine_detected(specs):
        cpu_cores = specs.cpu_cores
        ram_gb = specs.ram_gb
        print(f"🖥️  Machine detected: {cpu_cores} cores, {ram_gb:.1f}GB RAM")

    def on_task_complete(result):
        task_id = result.task_id
        status = "Success" if result.success else "Failed"
        print(f"📋 Task {task_id} completed: {status}")

    # Create orchestrator with callbacks
    orchestrator = create_research_orchestrator()
    orchestrator.set_research_callbacks(
        on_experiment_start=on_experiment_start,
        on_experiment_complete=on_experiment_complete,
        on_machine_detected=on_machine_detected,
        on_task_complete=on_task_complete,
    )

    print("Callbacks configured for research orchestrator")

    # Trigger machine detection to show callback
    orchestrator._detect_machine_specs()

    print("Callbacks example completed!\n")


async def main():
    """Run all examples."""
    print("ResearchOrchestrator Examples")
    print("=" * 50)

    try:
        # Run examples
        await simple_experiment_example()
        await research_workflow_example()
        await parallel_workers_example()
        callbacks_example()

        print("=" * 50)
        print("✅ All examples completed successfully!")

        print("\nTo use ResearchOrchestrator in your code:")
        print("```python")
        print("from equitrcoder import create_research_orchestrator, ExperimentConfig")
        print("")
        print("# Create orchestrator")
        print("orchestrator = create_research_orchestrator()")
        print("")
        print("# Create experiment config")
        print("config = ExperimentConfig(")
        print("    experiment_id='my_exp_001',")
        print("    name='My Experiment',")
        print("    description='Description of my experiment',")
        print("    hyperparameters={'batch_size': 32, 'epochs': 10}")
        print(")")
        print("")
        print("# Run experiment")
        print("result = await orchestrator.run_experiment(config)")
        print("```")

    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
