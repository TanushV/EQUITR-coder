"""
equitrcoder - Advanced AI coding assistant with Task Group System and Automatic Git Checkpoints.

This package provides a revolutionary dependency-aware task management system where:
- CleanOrchestrator creates structured JSON plans with task groups and dependencies
- Task groups have specializations (backend, frontend, database, testing, documentation)
- Single-agent mode executes groups sequentially based on dependencies
- Multi-agent mode executes groups in parallel phases
- Automatic git commits after each successful task group/phase completion
- Professional git history with conventional commit messages

Key Features:
- 🏗️ Dependency-Aware Architecture: Intelligent task group planning and execution
- 🤖 Automatic Git Checkpoints: Professional commit history with descriptive messages
- 📋 Structured JSON Planning: Sophisticated project decomposition
- 🔄 Phase-Based Execution: Parallel agents working on independent task groups
- 🎯 Session-Local Tracking: Isolated todo management per task

Quick Start:
    # Single agent with task groups and auto-commits
    from equitrcoder.modes.single_agent_mode import run_single_agent_mode
    result = await run_single_agent_mode(
        "Build a web server with authentication",
        auto_commit=True  # Automatic git commits
    )

    # Multi-agent with parallel phases and auto-commits
    from equitrcoder.modes.multi_agent_mode import run_multi_agent_parallel
    result = await run_multi_agent_parallel(
        "Build a complete web application",
        num_agents=3,
        auto_commit=True  # Automatic git commits after each phase
    )

    # Professional programmatic interface
    from equitrcoder import EquitrCoder, TaskConfiguration
    coder = EquitrCoder(git_enabled=True)
    config = TaskConfiguration(auto_commit=True)
    result = await coder.execute_task("Build an API", config)
"""

__version__ = "2.3.0"

from typing import List, Optional

# Core agent classes
from .agents import BaseAgent

# Clean Architecture Components
from .core import CleanAgent, CleanOrchestrator
from .core.config import Config, config_manager

# Core functionality
from .core.session import SessionData, SessionManagerV2
from .modes.multi_agent_mode import run_multi_agent_parallel, run_multi_agent_sequential
from .modes.single_agent_mode import run_single_agent_mode

# Programmatic Interface
from .programmatic import (
    EquitrCoder,
    ExecutionResult,
    MultiAgentTaskConfiguration,
    TaskConfiguration,
    create_multi_agent_coder,
    create_single_agent_coder,
)

# Tools
from .tools.base import Tool, ToolResult
from .tools.discovery import discover_tools

# Git Management
# Utility classes
from .utils import GitManager, RestrictedFileSystem, create_git_manager

__all__ = [
    # Version
    "__version__",
    # Agents
    "BaseAgent",
    # Clean Architecture
    "CleanOrchestrator",
    "CleanAgent",
    "run_single_agent_mode",
    "run_multi_agent_sequential",
    "run_multi_agent_parallel",
    # Utilities
    "RestrictedFileSystem",
    # Core
    "SessionManagerV2",
    "SessionData",
    "Config",
    "config_manager",
    # Tools
    "Tool",
    "ToolResult",
    "discover_tools",
    # Programmatic Interface
    "EquitrCoder",
    "TaskConfiguration",
    "MultiAgentTaskConfiguration",
    "ExecutionResult",
    "create_single_agent_coder",
    "create_multi_agent_coder",
    # Git Management
    "GitManager",
    "create_git_manager",
]


def create_single_agent(
    max_cost: Optional[float] = None,
    max_iterations: Optional[int] = None,
    tools: Optional[List[Tool]] = None,
) -> BaseAgent:
    """
    Convenience function to create a single agent with common settings.

    Args:
        max_cost: Maximum cost limit for the agent
        max_iterations: Maximum iterations for the agent
        tools: List of tools to add to the agent

    Returns:
        Configured BaseAgent instance
    """
    agent = BaseAgent(max_cost=max_cost, max_iterations=max_iterations)

    if tools:
        for tool in tools:
            agent.add_tool(tool)
    else:
        # Add default tools
        default_tools = discover_tools()
        for tool in default_tools:
            agent.add_tool(tool)

    return agent


async def run_task_single_agent(
    task_description: str,
    agent_model: str = "moonshot/kimi-k2-0711-preview",
    max_cost: Optional[float] = None,
    max_iterations: Optional[int] = None,
):
    """
    Convenience function to run a single agent task using clean architecture.

    Args:
        task_description: Description of the task to execute
        agent_model: Model to use for the agent
        max_cost: Maximum cost limit
        max_iterations: Maximum iterations

    Returns:
        Task execution result
    """
    return await run_single_agent_mode(
        task_description=task_description,
        agent_model=agent_model,
        audit_model=agent_model,
        max_cost=max_cost,
        max_iterations=max_iterations,
    )


async def run_task_multi_agent(
    task_description: str,
    num_agents: int = 2,
    agent_model: str = "moonshot/kimi-k2-0711-preview",
    max_cost_per_agent: Optional[float] = None,
):
    """
    Convenience function to run a multi-agent task using clean architecture.

    Args:
        task_description: Description of the task to execute
        num_agents: Number of agents to use
        agent_model: Model to use for agents
        max_cost_per_agent: Maximum cost limit per agent

    Returns:
        Task execution result
    """
    return await run_multi_agent_sequential(
        task_description=task_description,
        num_agents=num_agents,
        agent_model=agent_model,
        max_cost_per_agent=max_cost_per_agent,
    )


# Add convenience functions to __all__
__all__.extend(
    [
        "create_single_agent",
        "run_task_single_agent",
        "run_task_multi_agent",
    ]
)
