#!/usr/bin/env python3
"""
Basic test script for ResearchOrchestrator functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from equitrcoder import (
        ExperimentConfig,
        create_research_orchestrator,
        MachineSpecs,
    )

    print("✓ Successfully imported ResearchOrchestrator components")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


async def test_machine_detection():
    """Test machine specification detection."""
    print("\n=== Testing Machine Detection ===")

    orchestrator = create_research_orchestrator()
    specs = orchestrator._detect_machine_specs()

    print(f"OS Type: {specs.os_type}")
    print(f"CPU Cores: {specs.cpu_cores} (Physical: {specs.cpu_physical_cores})")
    print(f"RAM: {specs.ram_gb:.2f} GB")
    print(f"GPU Available: {specs.gpu_available}")
    if specs.gpu_available:
        print(f"GPU Count: {specs.gpu_count}")
        print(f"GPU Memory: {specs.gpu_memory_gb:.2f} GB")

    return specs


def test_parameter_scaling():
    """Test experiment parameter scaling."""
    print("\n=== Testing Parameter Scaling ===")

    orchestrator = create_research_orchestrator(scale_factor=0.8)

    # Mock machine specs for testing
    specs = MachineSpecs(
        os_type="posix",
        cpu_cores=4,
        cpu_physical_cores=2,
        ram_gb=8.0,
        gpu_available=True,
        gpu_count=1,
        gpu_memory_gb=6.0,
    )

    base_params = {
        "batch_size": 64,
        "epochs": 100,
        "learning_rate": 0.001,
        "num_workers": 8,
    }

    scaled_params = orchestrator._scale_experiment_params(base_params, specs)

    print("Base parameters:")
    for key, value in base_params.items():
        print(f"  {key}: {value}")

    print("\nScaled parameters:")
    for key, value in scaled_params.items():
        print(f"  {key}: {value}")

    return scaled_params


def test_dataset_validation():
    """Test dataset path validation."""
    print("\n=== Testing Dataset Validation ===")

    orchestrator = create_research_orchestrator()

    # Test existing path (current directory)
    current_dir = "."
    is_valid = orchestrator._validate_dataset_access(current_dir)
    print(f"Current directory '{current_dir}' validation: {is_valid}")

    # Test non-existent path
    fake_path = "/non/existent/path"
    is_valid = orchestrator._validate_dataset_access(fake_path)
    print(f"Fake path '{fake_path}' validation: {is_valid}")

    return True


def test_experiment_config():
    """Test experiment configuration creation."""
    print("\n=== Testing Experiment Configuration ===")

    config = ExperimentConfig(
        experiment_id="test_exp_001",
        name="Test Experiment",
        description="A test experiment for validation",
        dataset_path="./data",
        hyperparameters={
            "batch_size": 32,
            "epochs": 10,
            "learning_rate": 0.001,
        },
        environment_requirements=["torch", "numpy", "pandas"],
        expected_duration_mins=30,
        scale_factor=1.0,
    )

    print(f"Experiment ID: {config.experiment_id}")
    print(f"Name: {config.name}")
    print(f"Description: {config.description}")
    print(f"Hyperparameters: {config.hyperparameters}")

    return config


def test_orchestrator_status():
    """Test research orchestrator status reporting."""
    print("\n=== Testing Orchestrator Status ===")

    orchestrator = create_research_orchestrator(
        scale_factor=1.2, experiments_dir="./test_experiments"
    )

    # Detect machine specs first
    orchestrator._detect_machine_specs()

    status = orchestrator.get_research_status()

    print("Research Orchestrator Status:")
    for key, value in status.items():
        if isinstance(value, dict):
            print(f"  {key}: {dict}")
        else:
            print(f"  {key}: {value}")

    return status


async def main():
    """Run all tests."""
    print("Testing ResearchOrchestrator Implementation")
    print("=" * 50)

    try:
        # Test machine detection
        await test_machine_detection()

        # Test parameter scaling
        test_parameter_scaling()

        # Test dataset validation
        test_dataset_validation()

        # Test experiment config
        test_experiment_config()

        # Test orchestrator status
        test_orchestrator_status()

        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")

        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
