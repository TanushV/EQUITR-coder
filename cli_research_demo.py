#!/usr/bin/env python3
"""
CLI demonstration script for ResearchOrchestrator.

This script shows how ResearchOrchestrator can be integrated into command-line
interfaces and used both programmatically and interactively.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

from equitrcoder import (
    create_research_orchestrator,
    ExperimentConfig,
)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    """Print CLI banner."""
    print("=" * 60)
    print("  EQUITR-coder Research Agent Mode")
    print("  Machine-Aware ML Research Orchestrator")
    print("=" * 60)


async def cmd_detect_machine():
    """Command to detect and display machine specifications."""
    print("🔍 Detecting machine specifications...")

    orchestrator = create_research_orchestrator()
    specs = orchestrator._detect_machine_specs()

    print("\n📊 Machine Specifications:")
    print(f"  OS Type: {specs.os_type}")
    print(f"  CPU Cores: {specs.cpu_cores} (Physical: {specs.cpu_physical_cores})")
    print(f"  RAM: {specs.ram_gb:.2f} GB")
    print(f"  GPU Available: {'Yes' if specs.gpu_available else 'No'}")

    if specs.gpu_available:
        print(f"  GPU Count: {specs.gpu_count}")
        print(f"  GPU Memory: {specs.gpu_memory_gb:.2f} GB")

    print("\n✅ Machine detection completed")


async def cmd_scale_params(base_params: dict, scale_factor: float = 1.0):
    """Command to show parameter scaling for current machine."""
    print(f"⚖️  Scaling parameters with factor {scale_factor}...")

    orchestrator = create_research_orchestrator(scale_factor=scale_factor)
    specs = orchestrator._detect_machine_specs()
    scaled_params = orchestrator._scale_experiment_params(base_params, specs)

    print("\n📝 Parameter Scaling Results:")
    print("  Base Parameters:")
    for key, value in base_params.items():
        print(f"    {key}: {value}")

    print("  Scaled Parameters:")
    for key, value in scaled_params.items():
        print(f"    {key}: {value}")

    print("\n✅ Parameter scaling completed")


async def cmd_create_experiment(name: str, description: str, hyperparams: dict):
    """Command to create and validate an experiment configuration."""
    print(f"🧪 Creating experiment: {name}")

    config = ExperimentConfig(
        experiment_id=f"cli_exp_{int(asyncio.get_event_loop().time())}",
        name=name,
        description=description,
        hyperparameters=hyperparams,
    )

    print("\n📋 Experiment Configuration:")
    print(f"  ID: {config.experiment_id}")
    print(f"  Name: {config.name}")
    print(f"  Description: {config.description}")
    print("  Hyperparameters:")
    for key, value in (config.hyperparameters or {}).items():
        print(f"    {key}: {value}")

    # Show how it would be scaled
    orchestrator = create_research_orchestrator()
    specs = orchestrator._detect_machine_specs()
    scaled_params = orchestrator._scale_experiment_params(
        config.hyperparameters or {}, specs
    )

    print("  Scaled for current machine:")
    for key, value in scaled_params.items():
        print(f"    {key}: {value}")

    print("\n✅ Experiment configuration created")
    return config


async def cmd_status():
    """Command to show research orchestrator status."""
    print("📊 Research Orchestrator Status")

    orchestrator = create_research_orchestrator()
    orchestrator._detect_machine_specs()  # Populate machine specs

    status = orchestrator.get_research_status()

    print("\n🔧 Orchestrator Configuration:")
    print(f"  Type: {status.get('orchestrator_type', 'unknown')}")
    print(f"  Max Workers: {status.get('max_concurrent_workers', 0)}")
    print(f"  Cost Limit: ${status.get('cost_limit', 0.0):.2f}")
    print(f"  Iteration Limit: {status.get('iteration_limit', 0)}")
    print(f"  Scale Factor: {status.get('scale_factor', 1.0)}")

    print("\n📁 Experiment Tracking:")
    print(f"  Experiments Directory: {status.get('experiments_dir', 'unknown')}")
    print(f"  Total Experiments: {status.get('experiment_history_count', 0)}")
    print(f"  Successful: {status.get('successful_experiments', 0)}")
    print(f"  Failed: {status.get('failed_experiments', 0)}")

    machine_specs = status.get("machine_specs")
    if machine_specs:
        print("\n🖥️  Machine Specifications:")
        print(f"  CPU Cores: {machine_specs.get('cpu_cores', 'unknown')}")
        print(f"  RAM: {machine_specs.get('ram_gb', 0):.2f} GB")
        print(f"  GPU Available: {machine_specs.get('gpu_available', False)}")

    print("\n✅ Status check completed")


def cmd_interactive():
    """Interactive mode for exploring research orchestrator."""
    print("🎯 Interactive Research Mode")
    print("Enter commands to explore the research orchestrator:")
    print("  'machine' - Detect machine specs")
    print("  'scale' - Show parameter scaling")
    print("  'status' - Show orchestrator status")
    print("  'help' - Show this help")
    print("  'quit' - Exit interactive mode")

    while True:
        try:
            cmd = input("\nresearch> ").strip().lower()

            if cmd in ["quit", "exit", "q"]:
                print("👋 Exiting interactive mode")
                break
            elif cmd == "machine":
                asyncio.run(cmd_detect_machine())
            elif cmd == "scale":
                params = {
                    "batch_size": 64,
                    "epochs": 20,
                    "learning_rate": 0.001,
                    "num_workers": 4,
                }
                asyncio.run(cmd_scale_params(params))
            elif cmd == "status":
                asyncio.run(cmd_status())
            elif cmd == "help":
                print("Available commands:")
                print("  machine - Detect machine specifications")
                print("  scale   - Show parameter scaling example")
                print("  status  - Show orchestrator status")
                print("  help    - Show this help")
                print("  quit    - Exit interactive mode")
            else:
                print(f"Unknown command: {cmd}. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\n👋 Exiting interactive mode")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="EQUITR-coder Research Agent Mode CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s machine                    # Detect machine specs
  %(prog)s status                     # Show orchestrator status
  %(prog)s scale --params '{"batch_size": 64, "epochs": 10}'
  %(prog)s experiment --name "MNIST Test" --desc "Test experiment"
  %(prog)s interactive                # Start interactive mode
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Machine detection command
    subparsers.add_parser("machine", help="Detect machine specifications")

    # Status command
    subparsers.add_parser("status", help="Show orchestrator status")

    # Parameter scaling command
    scale_parser = subparsers.add_parser("scale", help="Show parameter scaling")
    scale_parser.add_argument(
        "--params",
        type=str,
        default='{"batch_size": 32, "epochs": 10, "learning_rate": 0.001}',
        help="JSON string of parameters to scale",
    )
    scale_parser.add_argument(
        "--scale-factor", type=float, default=1.0, help="Scale factor to apply"
    )

    # Experiment creation command
    exp_parser = subparsers.add_parser(
        "experiment", help="Create experiment configuration"
    )
    exp_parser.add_argument("--name", required=True, help="Experiment name")
    exp_parser.add_argument("--desc", required=True, help="Experiment description")
    exp_parser.add_argument(
        "--params",
        type=str,
        default='{"batch_size": 32, "epochs": 10}',
        help="JSON string of hyperparameters",
    )

    # Interactive mode
    subparsers.add_parser("interactive", help="Start interactive mode")

    args = parser.parse_args()

    print_banner()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "machine":
            await cmd_detect_machine()

        elif args.command == "status":
            await cmd_status()

        elif args.command == "scale":
            try:
                params = json.loads(args.params)
                await cmd_scale_params(params, args.scale_factor)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in --params: {e}")

        elif args.command == "experiment":
            try:
                params = json.loads(args.params)
                await cmd_create_experiment(args.name, args.desc, params)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in --params: {e}")

        elif args.command == "interactive":
            cmd_interactive()

    except Exception as e:
        print(f"❌ Command failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
