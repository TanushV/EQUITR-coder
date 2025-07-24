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

# Orchestrator classes
from .orchestrators import (
    SingleAgentOrchestrator,
    MultiAgentOrchestrator,
    WorkerConfig,
    TaskResult,
    ResearchOrchestrator,
    ExperimentConfig,
    ExperimentResult,
    MachineSpecs,
    create_research_orchestrator,
)

# Utility classes
from .utils import RestrictedFileSystem

# Core functionality
from .core.session import SessionManagerV2, SessionData
from .core.config import Config, config_manager

# Tools
from .tools.base import Tool, ToolResult
from .tools.discovery import discover_tools

__all__ = [
    # Version
    "__version__",
    # Agents
    "BaseAgent",
    "WorkerAgent",
    # Orchestrators
    "SingleAgentOrchestrator",
    "MultiAgentOrchestrator",
    "WorkerConfig",
    "TaskResult",
    "ResearchOrchestrator",
    "ExperimentConfig",
    "ExperimentResult",
    "MachineSpecs",
    "create_research_orchestrator",
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


def create_single_orchestrator(
    agent: BaseAgent = None, max_cost: float = None, max_iterations: int = None
) -> SingleAgentOrchestrator:
    """
    Convenience function to create a single agent orchestrator.

    Args:
        agent: BaseAgent to orchestrate (creates default if None)
        max_cost: Maximum cost limit
        max_iterations: Maximum iterations

    Returns:
        Configured SingleAgentOrchestrator instance
    """
    if agent is None:
        agent = create_single_agent(max_cost=max_cost, max_iterations=max_iterations)

    return SingleAgentOrchestrator(
        agent=agent, max_cost=max_cost, max_iterations=max_iterations
    )


def create_multi_orchestrator(
    max_concurrent_workers: int = 3,
    global_cost_limit: float = 10.0,
    max_total_iterations: int = 100,
) -> MultiAgentOrchestrator:
    """
    Convenience function to create a multi-agent orchestrator.

    Args:
        max_concurrent_workers: Maximum number of concurrent workers
        global_cost_limit: Global cost limit across all workers
        max_total_iterations: Maximum total iterations across all workers

    Returns:
        Configured MultiAgentOrchestrator instance
    """
    return MultiAgentOrchestrator(
        max_concurrent_workers=max_concurrent_workers,
        global_cost_limit=global_cost_limit,
        max_total_iterations=max_total_iterations,
    )


# Add convenience functions to __all__
__all__.extend(
    [
        "create_single_agent",
        "create_worker_agent",
        "create_single_orchestrator",
        "create_multi_orchestrator",
    ]
)
