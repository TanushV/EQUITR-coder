"""
Clean OOP Programmatic Interface for EQUITR Coder

This module provides a high-level, object-oriented interface for using EQUITR Coder
programmatically. It follows standard Python design patterns and conventions.
"""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import litellm

from ..agents.base_agent import BaseAgent
from ..agents.worker_agent import WorkerAgent
from ..core.config import Config, config_manager
from ..core.session import SessionData, SessionManagerV2
from ..modes.multi_agent_mode import (
    run_multi_agent_parallel,
    run_multi_agent_sequential,
)
from ..modes.single_agent_mode import run_single_agent_mode
from ..providers.litellm import LiteLLMProvider
from ..tools.discovery import discover_tools
from ..utils.git_manager import GitManager


@dataclass
class TaskConfiguration:
    """Configuration for a single task execution."""

    description: str
    max_cost: float = 2.0
    max_iterations: int = 20
    session_id: Optional[str] = None
    model: Optional[str] = None
    auto_commit: bool = True
    commit_message: Optional[str] = None


@dataclass
class MultiAgentTaskConfiguration:
    """Configuration for multi-agent task execution."""

    description: str
    max_workers: int = 3
    max_cost: float = 10.0
    supervisor_model: Optional[str] = None
    worker_model: Optional[str] = None
    auto_commit: bool = True
    commit_message: Optional[str] = None


@dataclass
class WorkerConfiguration:
    """Configuration for a worker agent."""

    worker_id: str
    scope_paths: List[str]
    allowed_tools: List[str]
    max_cost: float = 2.0
    max_iterations: int = 15
    description: Optional[str] = None


@dataclass
class ExecutionResult:
    """Result of task execution."""

    success: bool
    content: str
    cost: float
    iterations: int
    session_id: str
    execution_time: float
    error: Optional[str] = None
    git_committed: bool = False
    commit_hash: Optional[str] = None


class EquitrCoder:
    """
    Main programmatic interface for EQUITR Coder.

    This class provides a clean, OOP interface for executing AI coding tasks
    both in single-agent and multi-agent modes.

    Example:
        ```python
        # Single agent usage
        coder = EquitrCoder()
        result = await coder.execute_task("Fix the authentication bug")

        # Multi-agent usage
        multi_coder = EquitrCoder(mode="multi")
        result = await multi_coder.execute_task("Build a complete web application")
        ```
    """

    def __init__(
        self,
        mode: str = "single",
        repo_path: str = ".",
        config_path: Optional[str] = None,
        auto_discover_tools: bool = True,
        git_enabled: bool = True,
    ):
        """
        Initialize EQUITR Coder.

        Args:
            mode: Execution mode - 'single' or 'multi'
            repo_path: Path to the repository/project
            config_path: Optional path to configuration file
            auto_discover_tools: Whether to automatically discover tools
            git_enabled: Whether to enable git operations
        """
        self.mode = mode
        self.repo_path = Path(repo_path).resolve()
        self.git_enabled = git_enabled

        # Load configuration
        if config_path:
            self.config = config_manager.load_config(config_path)
        else:
            self.config = config_manager.load_config()

        # Initialize git manager
        if git_enabled:
            self.git_manager = GitManager(str(self.repo_path))
            self.git_manager.ensure_repo_ready()

        # Initialize session manager
        self.session_manager = SessionManagerV2(self.config.session.session_dir)

        # Discover tools if requested
        if auto_discover_tools:
            discover_tools()

        # Clean architecture doesn't need to maintain orchestrator instances
        # Each task execution creates fresh orchestrator + agent instances

        # Callbacks
        self.on_task_start: Optional[Callable] = None
        self.on_task_complete: Optional[Callable] = None
        self.on_tool_call: Optional[Callable] = None
        self.on_message: Optional[Callable] = None

    def check_available_api_keys(self) -> Dict[str, bool]:
        """Check which API keys are available in the environment."""
        providers = {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "azure": bool(os.getenv("AZURE_API_KEY")),
            "aws": bool(
                os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")
            ),
            "cohere": bool(os.getenv("COHERE_API_KEY")),
            # Add more providers as needed
        }
        return {
            provider: available
            for provider, available in providers.items()
            if available
        }

    async def check_model_availability(
        self, model: str, test_call: bool = False
    ) -> bool:
        """Check if a model is available and optionally verify with a test call."""
        try:
            # Basic check if model is supported by litellm
            if model not in litellm.model_list:
                return False

            if test_call:
                # Make a small test completion
                response = await litellm.acompletion(
                    model=model,
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=1,
                )
                return bool(response and response.choices)
            return True
        except Exception:
            return False

    async def execute_task(
        self,
        task_description: str,
        config: Optional[Union[TaskConfiguration, MultiAgentTaskConfiguration]] = None,
    ) -> ExecutionResult:
        """
        Execute a task using the configured mode.

        Args:
            task_description: Description of the task to execute
            config: Task configuration (TaskConfiguration for single, MultiAgentTaskConfiguration for multi)

        Returns:
            ExecutionResult with task outcome and metadata
        """
        start_time = datetime.now()

        try:
            if self.on_task_start:
                self.on_task_start(task_description, self.mode)

            if self.mode == "single":
                result = await self._execute_single_task(task_description, config)
            elif self.mode == "multi":
                result = await self._execute_multi_task(task_description, config)
            else:
                raise ValueError(f"Invalid mode: {self.mode}")

            # Handle git commit if requested
            if (
                result.success
                and config
                and getattr(config, "auto_commit", True)
                and self.git_enabled
            ):
                commit_msg = (
                    getattr(config, "commit_message", None)
                    or f"Complete task: {task_description}"
                )
                if self.git_manager.commit_task_completion(commit_msg):
                    result.git_committed = True
                    # Get the commit hash
                    recent_commits = self.git_manager.get_recent_commits(1)
                    if recent_commits:
                        result.commit_hash = recent_commits[0]["hash"]

            # Calculate execution time
            result.execution_time = (datetime.now() - start_time).total_seconds()

            if self.on_task_complete:
                self.on_task_complete(result)

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_result = ExecutionResult(
                success=False,
                content="",
                cost=0.0,
                iterations=0,
                session_id="error",
                execution_time=execution_time,
                error=str(e),
            )

            if self.on_task_complete:
                self.on_task_complete(error_result)

            return error_result

    async def _execute_single_task(
        self, task_description: str, config: Optional[TaskConfiguration]
    ) -> ExecutionResult:
        """Execute task in single-agent mode using clean architecture."""
        if not config:
            config = TaskConfiguration(description=task_description)

        try:
            # Set up callbacks for monitoring
            callbacks = {}
            if self.on_message:
                callbacks["on_message"] = self.on_message
            if self.on_tool_call:
                callbacks["on_tool_call"] = self.on_tool_call

            # Execute using clean single agent mode
            model = config.model or "moonshot/kimi-k2-0711-preview"
            result = await run_single_agent_mode(
                task_description=task_description,
                agent_model=model,
                audit_model=model,  # Use same model for audit
                project_path=self.repo_path,
                max_cost=config.max_cost,
                max_iterations=config.max_iterations,
                session_id=config.session_id,
                callbacks=callbacks,
            )

            return ExecutionResult(
                success=result["success"],
                content=result.get("execution_result", {}).get("final_message", "")
                or str(result.get("result", "")),
                cost=result.get("cost", 0.0),
                iterations=result.get("iterations", 0),
                session_id=result.get("session_id", ""),
                execution_time=0.0,  # Will be set by caller
                error=result.get("error"),
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                content="",
                cost=0.0,
                iterations=0,
                session_id="error",
                execution_time=0.0,
                error=str(e),
            )

    async def _execute_multi_task(
        self, task_description: str, config: Optional[MultiAgentTaskConfiguration]
    ) -> ExecutionResult:
        """Execute task in multi-agent mode using clean architecture."""
        if not config:
            config = MultiAgentTaskConfiguration(description=task_description)

        try:
            # Setup models
            supervisor_model = (
                config.supervisor_model or "moonshot/kimi-k2-0711-preview"
            )  # Default to kimi
            worker_model = config.worker_model or "moonshot/kimi-k2-0711-preview"

            print(f"🧠 Supervisor model: {supervisor_model}")
            print(f"🤖 Worker model: {worker_model}")

            # Set up callbacks for monitoring
            callbacks = {}
            if self.on_message:
                callbacks["on_message"] = self.on_message
            if self.on_tool_call:
                callbacks["on_tool_call"] = self.on_tool_call

            # Execute using clean multi-agent mode (sequential by default)
            result = await run_multi_agent_sequential(
                task_description=task_description,
                num_agents=config.max_workers,
                agent_model=worker_model,
                orchestrator_model=worker_model,
                supervisor_model=supervisor_model,
                audit_model=supervisor_model,
                project_path=self.repo_path,
                max_cost_per_agent=config.max_cost / config.max_workers,
                max_iterations_per_agent=None,  # Unlimited
                callbacks=callbacks,
            )

            return ExecutionResult(
                success=result["success"],
                content=str(result.get("agent_results", [])),
                cost=result.get("total_cost", 0.0),
                iterations=result.get("total_iterations", 0),
                session_id="multi_agent_session",
                execution_time=0.0,  # Will be set by caller
                error=result.get("error"),
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                content="",
                cost=0.0,
                iterations=0,
                session_id="error",
                execution_time=0.0,
                error=str(e),
            )

    def create_worker(self, config: WorkerConfiguration) -> WorkerAgent:
        """
        Create a worker agent with specified configuration.

        Args:
            config: Worker configuration

        Returns:
            Configured WorkerAgent instance
        """
        if self.mode != "multi":
            raise ValueError("Workers can only be created in multi-agent mode")

        return WorkerAgent(
            worker_id=config.worker_id,
            scope_paths=config.scope_paths,
            allowed_tools=config.allowed_tools,
            project_root=str(self.repo_path),
            max_cost=config.max_cost,
            max_iterations=config.max_iterations,
        )

    async def execute_parallel_tasks(
        self, tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tasks in parallel using clean architecture.

        Args:
            tasks: List of task dictionaries with keys like task_description

        Returns:
            List of execution results
        """
        results = []
        for task in tasks:
            # Use clean multi-agent parallel mode
            result = await run_multi_agent_parallel(
                task_description=task.get("task_description", ""),
                num_agents=task.get("num_agents", 2),
                agent_model="moonshot/kimi-k2-0711-preview",
            )
            results.append(result)
        return results

    def get_session_history(self, session_id: str) -> Optional[SessionData]:
        """Get session history by ID."""
        return self.session_manager.load_session(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions."""
        return self.session_manager.list_sessions()

    def get_git_status(self) -> Dict[str, Any]:
        """Get current git status."""
        if not self.git_enabled:
            return {"error": "Git is disabled"}
        return self.git_manager.get_status()

    def get_recent_commits(self, count: int = 5) -> List[Dict[str, str]]:
        """Get recent commit history."""
        if not self.git_enabled:
            return []
        return self.git_manager.get_recent_commits(count)

    async def cleanup(self):
        """Clean up resources."""
        # Clean architecture doesn't maintain persistent orchestrators
        # Nothing to clean up
        pass


# Convenience factory functions
def create_single_agent_coder(
    repo_path: str = ".",
    model: Optional[str] = "moonshot/kimi-k2-0711-preview",  # Default worker model
    git_enabled: bool = True,
) -> EquitrCoder:
    """
    Create a single-agent EQUITR Coder instance.

    Args:
        repo_path: Path to repository
        model: Model to use (default: moonshot/kimi-k2-0711-preview)
        git_enabled: Whether to enable git operations

    Returns:
        EquitrCoder instance configured for single-agent mode
    """
    return EquitrCoder(mode="single", repo_path=repo_path, git_enabled=git_enabled)


def create_multi_agent_coder(
    repo_path: str = ".",
    max_workers: int = 3,
    supervisor_model: Optional[str] = "o3",  # Strong model for supervisor
    worker_model: Optional[str] = "moonshot/kimi-k2-0711-preview",  # Worker model
    git_enabled: bool = True,
) -> EquitrCoder:
    """
    Create a multi-agent EQUITR Coder instance.

    Args:
        repo_path: Path to repository
        max_workers: Maximum number of concurrent workers
        supervisor_model: Model for supervisor agent (default: o3)
        worker_model: Model for worker agents (default: moonshot/kimi-k2-0711-preview)
        git_enabled: Whether to enable git operations

    Returns:
        EquitrCoder instance configured for multi-agent mode
    """
    return EquitrCoder(mode="multi", repo_path=repo_path, git_enabled=git_enabled)


# Legacy alias for backward compatibility
EquitrCoderAPI = EquitrCoder
