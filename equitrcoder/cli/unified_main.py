#!/usr/bin/env python3
"""
Unified CLI for equitrcoder with subcommands for different modes.
"""
import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

from ..agents.base_agent import BaseAgent
from ..agents.worker_agent import WorkerAgent
from ..orchestrators.single_orchestrator import SingleAgentOrchestrator
from ..orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator, WorkerConfig
from ..tools.discovery import discover_tools
from ..core.config import Config, config_manager


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="equitrcoder",
        description="Modular AI coding assistant supporting single and multi-agent workflows"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="equitrcoder 1.0.0"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Single agent command
    single_parser = subparsers.add_parser(
        "single",
        help="Run single agent mode"
    )
    single_parser.add_argument(
        "task",
        help="Task description for the agent"
    )
    single_parser.add_argument(
        "--model",
        help="Model to use (e.g., gpt-4, claude-3-sonnet)"
    )
    single_parser.add_argument(
        "--max-cost",
        type=float,
        help="Maximum cost limit"
    )
    single_parser.add_argument(
        "--max-iterations",
        type=int,
        help="Maximum iterations"
    )
    single_parser.add_argument(
        "--session-id",
        help="Session ID to resume"
    )
    
    # Multi agent command
    multi_parser = subparsers.add_parser(
        "multi",
        help="Run multi-agent mode"
    )
    multi_parser.add_argument(
        "coordination_task",
        help="High-level coordination task"
    )
    multi_parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Number of workers to create"
    )
    multi_parser.add_argument(
        "--supervisor-model",
        help="Model for supervisor agent"
    )
    multi_parser.add_argument(
        "--worker-model", 
        help="Model for worker agents"
    )
    multi_parser.add_argument(
        "--max-cost",
        type=float,
        default=10.0,
        help="Global cost limit"
    )
    
    # TUI command
    tui_parser = subparsers.add_parser(
        "tui",
        help="Launch interactive TUI"
    )
    tui_parser.add_argument(
        "--mode",
        choices=["single", "multi"],
        default="single",
        help="TUI mode"
    )
    
    # API command
    api_parser = subparsers.add_parser(
        "api",
        help="Start API server"
    )
    api_parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind to"
    )
    api_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to"
    )
    
    # Tools command
    tools_parser = subparsers.add_parser(
        "tools",
        help="Manage tools"
    )
    tools_parser.add_argument(
        "--list",
        action="store_true",
        help="List available tools"
    )
    tools_parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover and register tools"
    )
    
    return parser


async def run_single_agent(args) -> int:
    """Run single agent mode."""
    try:
        # Create base agent with basic tools
        agent = BaseAgent(
            max_cost=args.max_cost,
            max_iterations=args.max_iterations
        )
        
        # Discover and add tools
        tools = discover_tools()
        for tool in tools:
            agent.add_tool(tool)
        
        # Create orchestrator
        orchestrator = SingleAgentOrchestrator(
            agent=agent,
            max_cost=args.max_cost,
            max_iterations=args.max_iterations,
            model=args.model if args.model else 'gpt-4.1'
        )
        
        # Set up callbacks for monitoring
        def on_message(message_data):
            print(f"[{message_data['role']}] {message_data['content']}")
        
        def on_iteration(iteration, status):
            print(f"Iteration {iteration}: Cost ${status['current_cost']:.4f}")
        
        orchestrator.set_callbacks(
            on_message=on_message,
            on_iteration=on_iteration
        )
        
        print(f"🤖 Starting single agent task: {args.task}")
        
        # Execute task
        result = await orchestrator.execute_task(
            task_description=args.task,
            session_id=args.session_id
        )
        
        if result["success"]:
            print(f"✅ Task completed successfully!")
            print(f"💰 Total cost: ${result['cost']:.4f}")
            print(f"🔄 Iterations: {result['iterations']}")
            print(f"📝 Session ID: {result['session_id']}")
            return 0
        else:
            print(f"❌ Task failed: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


async def run_multi_agent(args) -> int:
    """Run multi-agent mode."""
    try:
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator(
            max_concurrent_workers=args.workers,
            global_cost_limit=args.max_cost
        )
        
        # Create workers
        worker_configs = []
        for i in range(args.workers):
            config = WorkerConfig(
                worker_id=f"worker_{i+1}",
                scope_paths=["."],  # Allow access to current directory
                allowed_tools=["read_file", "edit_file", "run_cmd", "ask_supervisor"],
                max_cost=args.max_cost / args.workers,
                max_iterations=10
            )
            worker_configs.append(config)
            orchestrator.create_worker(config)
        
        # Set up callbacks
        def on_task_start(task_id, worker_id, description):
            print(f"🚀 {worker_id} starting task {task_id}: {description}")
        
        def on_task_complete(task_result):
            status = "✅" if task_result.success else "❌"
            print(f"{status} {task_result.worker_id} completed {task_result.task_id} "
                  f"(${task_result.cost:.4f}, {task_result.execution_time:.2f}s)")
        
        orchestrator.set_callbacks(
            on_task_start=on_task_start,
            on_task_complete=on_task_complete
        )
        
        print(f"🤖 Starting multi-agent coordination: {args.coordination_task}")
        print(f"👥 Workers: {args.workers}")
        
        # Create example worker tasks
        worker_tasks = []
        for i, config in enumerate(worker_configs):
            worker_tasks.append({
                "task_id": f"subtask_{i+1}",
                "worker_id": config.worker_id,
                "task_description": f"Part {i+1} of: {args.coordination_task}",
                "context": {"part": i+1, "total_parts": len(worker_configs)}
            })
        
        # Execute coordination
        result = await orchestrator.coordinate_workers(
            coordination_task=args.coordination_task,
            worker_tasks=worker_tasks
        )
        
        if result["success"]:
            print(f"✅ Coordination completed successfully!")
            print(f"💰 Total cost: ${result['total_cost']:.4f}")
            print(f"⏱️  Total time: {result['total_time']:.2f}s")
            return 0
        else:
            print(f"❌ Coordination failed: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def run_tui(args) -> int:
    """Launch TUI mode."""
    try:
        print(f"🖥️  Launching TUI in {args.mode} mode...")
        # Import TUI here to avoid dependency issues
        from ..ui.tui import launch_tui
        return launch_tui(mode=args.mode)
    except ImportError:
        print("❌ TUI dependencies not available. Install with: pip install equitrcoder[tui]")
        return 1
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
        print("❌ API dependencies not available. Install with: pip install equitrcoder[api]")
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


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        args.command = "tui"
        args.mode = "single"  # Default to single mode for TUI
    
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