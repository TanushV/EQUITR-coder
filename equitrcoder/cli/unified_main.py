#!/usr/bin/env python3
"""
Unified CLI for equitrcoder with subcommands for different modes.
"""
import argparse
import asyncio
import sys

from ..core.config import config_manager
from ..modes.multi_agent_mode import (
    run_multi_agent_parallel,
)
from ..modes.single_agent_mode import run_single_agent_mode
from ..tools.discovery import discover_tools
from ..ui.tui import SimpleTUI


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="equitrcoder",
        description="Modular AI coding assistant supporting single and multi-agent workflows",
    )

    parser.add_argument("--version", action="version", version="equitrcoder 1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Single agent command
    single_parser = subparsers.add_parser("single", help="Run single agent mode")
    single_parser.add_argument("task", help="Task description for the agent")
    single_parser.add_argument(
        "--model", help="Model to use (e.g., gpt-4, claude-3-sonnet)"
    )
    single_parser.add_argument("--max-cost", type=float, help="Maximum cost limit")
    single_parser.add_argument("--max-iterations", type=int, help="Maximum iterations")
    single_parser.add_argument("--session-id", help="Session ID to resume")

    # Multi agent command
    multi_parser = subparsers.add_parser("multi", help="Run multi-agent mode")
    multi_parser.add_argument("coordination_task", help="High-level coordination task")
    multi_parser.add_argument(
        "--team",
        help="Comma-separated list of specialist profiles to use (e.g., backend_dev,frontend_dev)"
    )
    multi_parser.add_argument(
        "--workers", type=int, default=2, help="Number of workers to create"
    )
    multi_parser.add_argument("--supervisor-model", help="Model for supervisor agent")
    multi_parser.add_argument("--worker-model", help="Model for worker agents")
    multi_parser.add_argument(
        "--max-cost", type=float, default=10.0, help="Global cost limit"
    )

    # TUI command
    tui_parser = subparsers.add_parser("tui", help="Launch interactive TUI")
    tui_parser.add_argument(
        "--mode", choices=["single", "multi"], default="single", help="TUI mode"
    )

    # API command
    api_parser = subparsers.add_parser("api", help="Start API server")
    api_parser.add_argument("--host", default="localhost", help="Host to bind to")
    api_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")

    # Tools command
    tools_parser = subparsers.add_parser("tools", help="Manage tools")
    tools_parser.add_argument(
        "--list", action="store_true", help="List available tools"
    )
    tools_parser.add_argument(
        "--discover", action="store_true", help="Discover and register tools"
    )

    # Models command
    models_parser = subparsers.add_parser("models", help="List available AI models")
    models_parser.add_argument(
        "--provider", help="Filter by provider (moonshot, openai, etc.)"
    )

    return parser


async def run_single_agent(args) -> int:
    """Run single agent mode using clean architecture."""
    try:
        # Set up callbacks for live monitoring
        def on_message(message_data):
            role = message_data["role"].upper()
            content = message_data["content"]
            print(f"\n[{role}] {content}")
            if role == "ASSISTANT":
                print("-" * 50)

        def on_iteration(iteration, status):
            print(f"🔄 Iteration {iteration}: Cost=${status.get('cost', 0):.4f}")

        def on_tool_call(tool_data):
            if tool_data.get("success", True):
                tool_name = tool_data.get("tool_name", "unknown")
                print(f"🔧 Using tool: {tool_name}")
            else:
                print(f"❌ Tool error: {tool_data.get('error', 'unknown')}")

        callbacks = {
            "on_message": on_message,
            "on_iteration": on_iteration,
            "on_tool_call": on_tool_call,
        }

        print(f"🤖 Starting single agent task: {args.task}")
        print("=" * 60)

        # Use clean single agent mode (same as programmatic)
        model = args.model or "moonshot/kimi-k2-0711-preview"
        result = await run_single_agent_mode(
            task_description=args.task,
            agent_model=model,
            orchestrator_model=model,  # Add missing orchestrator_model
            audit_model=model,
            max_cost=args.max_cost,
            max_iterations=args.max_iterations,
            auto_commit=True,  # Add missing auto_commit
            project_path=".",  # Add missing project_path
            callbacks=callbacks,
        )

        print("=" * 60)
        if result["success"]:
            print("✅ Task completed successfully!")
            print(f"💰 Total cost: ${result.get('cost', 0):.4f}")
            print(f"🔄 Iterations: {result.get('iterations', 0)}")
            print(f"📝 Session ID: {result.get('session_id', 'N/A')}")
            audit_result = result.get("audit_result", {})
            if audit_result.get("audit_passed"):
                print("🔍 ✅ Audit: PASSED")
            else:
                print("🔍 ❌ Audit: FAILED")
            return 0
        else:
            print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


async def run_multi_agent(args) -> int:
    """Run multi-agent mode using clean architecture."""
    try:
        # Set up callbacks for monitoring
        def on_message(message_data):
            role = message_data["role"].upper()
            content = message_data["content"]
            print(f"\n[{role}] {content}")
            if role == "ASSISTANT":
                print("-" * 50)

        def on_iteration(iteration, status):
            print(f"🔄 Iteration {iteration}: Cost=${status.get('cost', 0):.4f}")

        def on_tool_call(tool_data):
            if tool_data.get("success", True):
                tool_name = tool_data.get("tool_name", "unknown")
                print(f"🔧 Using tool: {tool_name}")
            else:
                print(f"❌ Tool error: {tool_data.get('error', 'unknown')}")

        callbacks = {
            "on_message": on_message,
            "on_iteration": on_iteration,
            "on_tool_call": on_tool_call,
        }

        print(
            f"🤖 Starting multi-agent task with {args.workers} agents: {args.coordination_task}"
        )
        print("=" * 60)

        # Parse the team argument
        team = args.team.split(',') if args.team else None

        # Use clean multi-agent parallel mode (same as programmatic)
        supervisor_model = args.supervisor_model or "moonshot/kimi-k2-0711-preview"
        worker_model = args.worker_model or "moonshot/kimi-k2-0711-preview"

        result = await run_multi_agent_parallel(
            task_description=args.coordination_task,
            team=team,
            num_agents=args.workers,
            agent_model=worker_model,
            orchestrator_model=supervisor_model,  # Use supervisor for orchestrator
            audit_model=supervisor_model,
            max_cost_per_agent=args.max_cost / args.workers,
            max_iterations_per_agent=50,  # Add missing parameter
            run_parallel=True,
            auto_commit=True,
            callbacks=callbacks,
        )

        print("=" * 60)
        if result["success"]:
            print("✅ Multi-agent task completed successfully!")
            print(f"💰 Total cost: ${result.get('total_cost', 0):.4f}")
            print(f"🔄 Total iterations: {result.get('total_iterations', 0)}")
            print(f"👥 Agents used: {result.get('num_agents', 0)}")
            return 0
        else:
            print(f"❌ Multi-agent task failed: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def run_tui(args) -> int:
    """Launch TUI mode."""
    try:
        print("🖥️  Launching Interactive TUI...")

        # Load configuration and start SimpleTUI
        config = config_manager.load_config()
        tui = SimpleTUI(config)

        # Run the TUI in async context
        async def run_tui_async():
            return await tui.run()

        import asyncio

        asyncio.run(run_tui_async())
        return 0

    except Exception as e:
        print(f"❌ TUI Error: {e}")
        return 1


def run_api(args) -> int:
    """Start API server."""
    try:
        print(f"🌐 Starting API server on {args.host}:{args.port}...")
        # Import API here to avoid dependency issues
        from ..api import start_server

        start_server(host=args.host, port=args.port)
        return 0
    except ImportError:
        print(
            "❌ API dependencies not available. Install with: pip install equitrcoder[api]"
        )
        return 1
    except Exception as e:
        print(f"❌ API Error: {e}")
        return 1


def run_tools(args) -> int:
    """Manage tools."""
    try:
        if args.list:
            print("🔧 Available tools:")
            tools = discover_tools()
            for tool in tools:
                print(f"  - {tool.get_name()}: {tool.get_description()}")
            return 0

        if args.discover:
            print("🔍 Discovering tools...")
            tools = discover_tools()
            print(f"Found {len(tools)} tools")
            return 0

        print("Use --list or --discover")
        return 1

    except Exception as e:
        print(f"❌ Tools Error: {e}")
        return 1


def run_models(args) -> int:
    """List available AI models."""
    try:
        print("🤖 Available AI Models:")

        # Common models organized by provider
        models = {
            "moonshot": [
                "moonshot/kimi-k2-0711-preview",
                "moonshot/kimi-k1-32k",
                "moonshot/kimi-k1-128k",
            ],
            "openai": [
                "openai/gpt-4",
                "openai/gpt-4-turbo",
                "openai/gpt-3.5-turbo",
                "o3",  # Special model
                "o1",
            ],
            "anthropic": [
                "anthropic/claude-3-sonnet",
                "anthropic/claude-3-haiku",
                "anthropic/claude-3-opus",
            ],
            "other": ["gemini/gemini-pro", "cohere/command-r", "mistral/mistral-7b"],
        }

        # Filter by provider if specified
        if args.provider:
            provider = args.provider.lower()
            if provider in models:
                print(f"\n{provider.upper()} Models:")
                for model in models[provider]:
                    print(f"  - {model}")
            else:
                print(f"❌ Unknown provider: {provider}")
                print(f"Available providers: {', '.join(models.keys())}")
                return 1
        else:
            # Show all models
            for provider, model_list in models.items():
                print(f"\n{provider.upper()} Models:")
                for model in model_list:
                    print(f"  - {model}")

        print("\n💡 Usage: equitrcoder single 'your task' --model <model_name>")
        print("💡 Recommended: moonshot/kimi-k2-0711-preview (cost-effective)")
        print("💡 For complex tasks: o3 (more expensive but powerful)")

        return 0

    except Exception as e:
        print(f"❌ Models Error: {e}")
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        args.command = "tui"
        args.mode = "single"  # Default to single mode for TUI

    # Validate model requirements for CLI modes only
    if args.command == "single":
        if not hasattr(args, "model") or not args.model:
            print("❌ Error: --model is required for single agent mode")
            print(
                "Example: equitrcoder single 'task' --model moonshot/kimi-k2-0711-preview"
            )
            return 1
    elif args.command == "multi":
        if not hasattr(args, "supervisor_model") or not args.supervisor_model:
            print("❌ Error: --supervisor-model is required for multi-agent mode")
            return 1
        if not hasattr(args, "worker_model") or not args.worker_model:
            print("❌ Error: --worker-model is required for multi-agent mode")
            return 1
    # TUI handles model selection internally - no validation needed

    try:
        if args.command == "single":
            return asyncio.run(run_single_agent(args))
        elif args.command == "multi":
            return asyncio.run(run_multi_agent(args))
        elif args.command == "tui":
            return run_tui(args)
        elif args.command == "api":
            return run_api(args)
        elif args.command == "tools":
            return run_tools(args)
        elif args.command == "models":
            return run_models(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
