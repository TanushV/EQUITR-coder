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
        
        # Create orchestrator - no default model fallback
        orchestrator = SingleAgentOrchestrator(
            agent=agent,
            model=args.model,  # Required, no fallback
            session_manager=None,
            max_cost=args.max_cost,
            max_iterations=args.max_iterations
        )
        
        # Set up callbacks for live monitoring
        def on_message(message_data):
            role = message_data['role'].upper()
            content = message_data['content']
            print(f"\n[{role}] {content}")
            if role == "ASSISTANT":
                print("-" * 50)
        
        def on_tool_call(tool_data):
            if tool_data.get('success', True):
                tool_name = tool_data.get('tool_name', 'unknown')
                print(f"🔧 Using tool: {tool_name}")
            else:
                print(f"❌ Tool error: {tool_data.get('error', 'unknown')}")
        
        orchestrator.set_callbacks(
            on_message=on_message
        )
        
        # Set tool callback on agent
        agent.on_tool_call_callback = on_tool_call
        
        print(f"🤖 Starting single agent task: {args.task}")
        print("=" * 60)
        
        # Execute task
        result = await orchestrator.execute_task(
            task_description=args.task,
            session_id=args.session_id
        )
        
        print("=" * 60)
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
        from ..providers.litellm import LiteLLMProvider
        from ..orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator, WorkerConfig
        from ..agents.base_agent import BaseAgent
        from ..tools.discovery import discover_tools
        
        # Create providers for supervisor and worker
        supervisor_provider = LiteLLMProvider(model=args.supervisor_model)
        worker_provider = LiteLLMProvider(model=args.worker_model)
        
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator(
            supervisor_provider=supervisor_provider,
            worker_provider=worker_provider,
            max_concurrent_workers=args.workers,
            global_cost_limit=args.max_cost
        )
        
        # Create worker agents
        worker_configs = []
        for i in range(args.workers):
            # Create base agent for each worker
            agent = BaseAgent(
                agent_id=f"worker_{i+1}",
                max_cost=args.max_cost / args.workers,
                max_iterations=10
            )
            
            # Discover and add tools
            tools = discover_tools()
            for tool in tools:
                agent.add_tool(tool)
            
            config = WorkerConfig(
                worker_id=f"worker_{i+1}",
                scope_paths=["."],  # Allow access to current directory
                allowed_tools=["create_file", "edit_file", "read_file", "list_files", "run_command", "git_commit", "git_status", "send_agent_message", "receive_agent_messages", "get_message_history", "get_active_agents"],
                max_cost=args.max_cost / args.workers,
                max_iterations=10
            )
            worker_configs.append(config)
            
            # Create worker with the base agent
            worker = orchestrator.create_worker(config, worker_provider)
            
            # Transfer tools from base agent to worker
            for tool_name, tool in agent.tool_registry.items():
                worker.add_tool(tool)
        
        # Set up callbacks for live monitoring
        def on_task_start(task_id, worker_id, description):
            print(f"🚀 {worker_id} starting task {task_id}: {description}")
        
        def on_task_complete(task_result):
            status = "✅" if task_result.success else "❌"
            print(f"{status} {task_result.worker_id} completed {task_result.task_id} "
                  f"(💰${task_result.cost:.4f}, ⏱️{task_result.execution_time:.2f}s)")
            if not task_result.success:
                print(f"   Error: {task_result.error}")
        
        def on_worker_message(message_data):
            role = message_data['role'].upper()
            content = message_data['content'][:100] + "..." if len(message_data['content']) > 100 else message_data['content']
            worker_id = message_data.get('agent_id', 'unknown')
            print(f"💬 {worker_id} [{role}]: {content}")
        
        orchestrator.set_callbacks(
            on_task_start=on_task_start,
            on_task_complete=on_task_complete,
            on_worker_message=on_worker_message
        )
        
        print(f"🤖 Starting multi-agent coordination: {args.coordination_task}")
        print(f"👥 Workers: {args.workers}")
        print(f"🧠 Supervisor Model: {args.supervisor_model}")
        print(f"⚡ Worker Model: {args.worker_model}")
        print("=" * 60)
        
        # Create worker tasks by breaking down the main task
        worker_tasks = []
        task_parts = [
            f"Part {i+1} of {args.workers}: {args.coordination_task}",
            f"Focus on implementation aspect {i+1} of the overall task: {args.coordination_task}",
            f"Handle component {i+1} for: {args.coordination_task}",
        ]
        
        for i, config in enumerate(worker_configs):
            task_description = task_parts[i % len(task_parts)]
            worker_tasks.append({
                "task_id": f"subtask_{i+1}",
                "worker_id": config.worker_id,
                "task_description": task_description,
                "context": {"part": i+1, "total_parts": len(worker_configs)}
            })
        
        # Execute coordination
        result = await orchestrator.coordinate_workers(
            coordination_task=args.coordination_task,
            worker_tasks=worker_tasks
        )
        
        print("=" * 60)
        if result["success"]:
            print(f"✅ Coordination completed successfully!")
            print(f"💰 Total cost: ${result['total_cost']:.4f}")
            print(f"⏱️  Total time: {result['total_time']:.2f}s")
            
            # Show worker results summary
            successful_workers = sum(1 for r in result['worker_results'] if r.success)
            print(f"👥 Workers: {successful_workers}/{len(result['worker_results'])} successful")
            
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
        # Import TUI here - no dependency issues with simple ASCII TUI
        from ..ui.tui import launch_tui
        return launch_tui(mode=args.mode)
    except Exception as e:
        print(f"❌ Error: {e}")
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
    
    # Validate model requirements for CLI modes only
    if args.command == "single":
        if not hasattr(args, 'model') or not args.model:
            print("❌ Error: --model is required for single agent mode")
            print("Example: equitrcoder single 'task' --model moonshot/kimi-k2-0711-preview")
            return 1
    elif args.command == "multi":
        if not hasattr(args, 'supervisor_model') or not args.supervisor_model:
            print("❌ Error: --supervisor-model is required for multi-agent mode")
            return 1
        if not hasattr(args, 'worker_model') or not args.worker_model:
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