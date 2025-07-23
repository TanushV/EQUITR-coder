import argparse
import sys
import asyncio
from typing import List

from equitrcoder.cli.model_cli import ModelCLI
from equitrcoder.audit.audit_phase import run_audit
from equitrcoder.orchestrator.multi_agent_orchestrator import run_multi_agent_workflow
from equitrcoder.config.model_config import get_config_manager


class MainCLI:
    def __init__(self):
        self.config_manager = get_config_manager()

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="OpenCode Multi-Agent CLI")
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Model configuration
        model_parser = subparsers.add_parser(
            "model", help="Model configuration commands"
        )
        model_subparsers = model_parser.add_subparsers(dest="model_command")

        # Model mode
        mode_parser = model_subparsers.add_parser("mode", help="Set model mode")
        mode_parser.add_argument("mode", choices=["single", "multi"], help="Model mode")

        # Model selection
        models_parser = model_subparsers.add_parser("models", help="Set models")
        models_parser.add_argument("primary", help="Primary model")
        models_parser.add_argument("--secondary", help="Secondary model for multi-mode")

        # Show config
        show_parser = model_subparsers.add_parser(
            "show", help="Show current configuration"
        )

        # Multi-agent workflow
        workflow_parser = subparsers.add_parser(
            "workflow", help="Run multi-agent workflow"
        )
        workflow_parser.add_argument(
            "--project-root", default=".", help="Project root directory"
        )

        # Audit
        audit_parser = subparsers.add_parser("audit", help="Run audit phase")
        audit_parser.add_argument(
            "--project-root", default=".", help="Project root directory"
        )
        audit_parser.add_argument(
            "--mode", choices=["final", "periodic"], default="final", help="Audit mode"
        )

        # Status
        status_parser = subparsers.add_parser("status", help="Show system status")

        return parser

    def run(self, args: List[str] = None):
        if args is None:
            args = sys.argv[1:]

        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        if parsed_args.command == "model":
            self.handle_model_command(parsed_args)
        elif parsed_args.command == "workflow":
            asyncio.run(self.run_workflow(parsed_args))
        elif parsed_args.command == "audit":
            asyncio.run(self.run_audit(parsed_args))
        elif parsed_args.command == "status":
            self.show_status()
        else:
            parser.print_help()

    def handle_model_command(self, args):
        """Handle model configuration commands."""
        model_cli = ModelCLI()

        if args.model_command == "mode":
            model_cli.set_mode(args.mode)
        elif args.model_command == "models":
            model_cli.set_models(args.primary, args.secondary)
        elif args.model_command == "show":
            model_cli.show_config()
        else:
            # Delegate to model CLI for subcommands
            model_cli.run([args.model_command] + sys.argv[3:])

    async def run_workflow(self, args):
        """Run the multi-agent workflow."""
        print("Starting multi-agent workflow...")
        result = await run_multi_agent_workflow(args.project_root)

        print(f"Workflow completed:")
        print(f"  Tasks completed: {result.get('tasks_completed', 0)}")
        print(f"  Tasks failed: {result.get('tasks_failed', 0)}")

        if result.get("results"):
            for r in result["results"]:
                if "error" in r:
                    print(f"  Task {r['task_id']} failed: {r['error']}")
                else:
                    print(f"  Task {r['task_id']} completed successfully")

    async def run_audit(self, args):
        """Run the audit phase."""
        print("Running audit...")
        result = run_audit(args.project_root)

        print(f"Audit results:")
        print(f"  Audit passed: {result.get('audit_passed', False)}")
        print(f"  Tests passed: {result.get('tests', {}).get('passed', False)}")
        print(f"  Linting passed: {result.get('linting', {}).get('passed', False)}")
        print(f"  Git clean: {result.get('git_status', {}).get('clean', False)}")

        if result.get("new_tasks"):
            print(f"  New tasks generated: {len(result['new_tasks'])}")
            for task in result["new_tasks"]:
                print(f"    - {task['title']} (assigned to {task['assigned_to']})")

    def show_status(self):
        """Show system status."""
        config = self.config_manager.get_config()

        print("EQUITR-coder Multi-Agent System Status:")
        print()
        print("Model Configuration:")
        print(f"  Mode: {config.mode}")
        print(f"  Primary Model: {config.primary_model}")
        if config.secondary_model:
            print(f"  Secondary Model: {config.secondary_model}")
        print(f"  Active Models: {', '.join(config.models)}")
        print()

        print("Available Commands:")
        print("  opencode model mode <single|multi>     - Set model mode")
        print("  opencode model models <primary> [--secondary <model>]  - Set models")
        print("  opencode model show                    - Show current config")
        print("  opencode workflow                      - Run multi-agent workflow")
        print("  opencode audit                         - Run audit phase")
        print("  opencode status                        - Show system status")


def main():
    cli = MainCLI()
    cli.run()


if __name__ == "__main__":
    main()
