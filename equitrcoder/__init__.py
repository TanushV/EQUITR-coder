"""
equitrcoder - Modular AI coding assistant supporting single and multi-agent workflows.

This package provides a clean, modular architecture where:
- BaseAgent provides common functionality for all agents
- WorkerAgent adds restricted file system access for security
- SingleAgentOrchestrator wraps BaseAgent for simple tasks
- MultiAgentOrchestrator coordinates multiple WorkerAgents for complex tasks

Quick Start:
    # Single agent
    from equitrcoder import BaseAgent, SingleAgentOrchestrator
    agent = BaseAgent()
    orchestrator = SingleAgentOrchestrator(agent)
    result = await orchestrator.execute_task("Fix the bug in main.py")

    # Multi agent
    from equitrcoder import MultiAgentOrchestrator, WorkerConfig
    orchestrator = MultiAgentOrchestrator()
    config = WorkerConfig("worker1", ["src/"], ["read_file", "edit_file"])
    worker = orchestrator.create_worker(config)
    result = await orchestrator.execute_task("task1", "worker1", "Refactor module")
"""

__version__ = "1.0.0"

# Core agent classes
from .agents import BaseAgent, WorkerAgent

# Clean Architecture Components
from .core import CleanOrchestrator, CleanAgent
from .modes.single_agent_mode import run_single_agent_mode
from .modes.multi_agent_mode import run_multi_agent_sequential, run_multi_agent_parallel

# Utility classes
from .utils import RestrictedFileSystem

# Core functionality
from .core.session import SessionManagerV2, SessionData
from .core.config import Config, config_manager

# Tools
from .tools.base import Tool, ToolResult
from .tools.discovery import discover_tools

# Programmatic Interface
from .programmatic import (
    EquitrCoder,
    EquitrCoderAPI,
    TaskConfiguration,
    MultiAgentTaskConfiguration,
    WorkerConfiguration,
    ExecutionResult,
    create_single_agent_coder,
    create_multi_agent_coder
)

# Git Management
from .utils import GitManager, create_git_manager

__all__ = [
    # Version
    "__version__",
    # Agents
    "BaseAgent",
    "WorkerAgent",
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
    "EquitrCoderAPI",
    "TaskConfiguration",
    "MultiAgentTaskConfiguration", 
    "WorkerConfiguration",
    "ExecutionResult",
    "create_single_agent_coder",
    "create_multi_agent_coder",
    # Git Management
    "GitManager",
    "create_git_manager",
]


def create_single_agent(
    max_cost: float = None, max_iterations: int = None, tools: list = None
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


def create_worker_agent(
    worker_id: str,
    scope_paths: list,
    allowed_tools: list,
    max_cost: float = None,
    max_iterations: int = None,
    project_root: str = ".",
) -> WorkerAgent:
    """
    Convenience function to create a worker agent with restricted access.

    Args:
        worker_id: Unique identifier for the worker
        scope_paths: List of paths the worker can access
        allowed_tools: List of tools the worker can use
        max_cost: Maximum cost limit for the worker
        max_iterations: Maximum iterations for the worker
        project_root: Root directory for the project

    Returns:
        Configured WorkerAgent instance
    """
    return WorkerAgent(
        worker_id=worker_id,
        scope_paths=scope_paths,
        allowed_tools=allowed_tools,
        project_root=project_root,
        max_cost=max_cost,
        max_iterations=max_iterations,
    )


async def run_task_single_agent(
    task_description: str,
    agent_model: str = "moonshot/kimi-k2-0711-preview",
    max_cost: float = None,
    max_iterations: int = None
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
        max_iterations=max_iterations
    )


async def run_task_multi_agent(
    task_description: str,
    num_agents: int = 2,
    agent_model: str = "moonshot/kimi-k2-0711-preview",
    max_cost_per_agent: float = None
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
        max_cost_per_agent=max_cost_per_agent
    )


# Add convenience functions to __all__
__all__.extend(
    [
        "create_single_agent",
        "create_worker_agent", 
        "run_task_single_agent",
        "run_task_multi_agent",
    ]
)
