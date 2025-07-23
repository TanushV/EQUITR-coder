"""
EQUITR Coder Programmatic API

This module provides a programmatic interface for using EQUITR Coder in your code.
"""

import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path

from .core.config import config_manager
from .core.orchestrator import AgentOrchestrator
from .tools.builtin.todo import todo_manager, TodoItem
from .utils.env_loader import auto_load_environment


class EquitrAPI:
    """
    Programmatic API for EQUITR Coder.

    This class provides an easy-to-use interface for integrating EQUITR Coder
    into your Python applications.
    """

    def __init__(
        self,
        repo_path: str = ".",
        profile: str = "default",
        model: Optional[str] = None,
        budget: Optional[float] = None,
        api_key: Optional[str] = None,
        multi_agent: bool = False,
        supervisor_model: Optional[str] = None,
        worker_model: Optional[str] = None,
        log_tool_calls: bool = False,
        tool_log_file: str = "tool_calls.log",
        debug: bool = False,
    ):
        """
        Initialize the EQUITR API.

        Args:
            repo_path: Path to the repository to analyze
            profile: Configuration profile to use (default, ml_researcher, app_developer)
            model: LLM model to use (overrides config)
            budget: Budget limit in USD (overrides config)
            api_key: API key for the LLM provider (if not set in environment)
            multi_agent: Enable multi-agent mode
            supervisor_model: Model to use for supervisor in multi-agent mode
            worker_model: Model to use for workers in multi-agent mode
            log_tool_calls: Enable tool call logging
            tool_log_file: File path for tool call logs
            debug: Enable debug mode with live LLM responses and tool call output
        """
        self.repo_path = Path(repo_path).resolve()
        self.profile = profile
        self.debug = debug

        # Auto-load environment variables from .env file
        env_status = auto_load_environment()
        if self.debug and env_status["dotenv_loaded"]:
            print(
                f"🔑 Loaded {env_status['available_providers']} API providers from .env file"
            )

        # Load configuration
        self.config = config_manager.load_config(profile)

        # Store model overrides (do not mutate config)
        self._model_override = model
        self._supervisor_model_override = supervisor_model
        self._worker_model_override = worker_model

        if budget:
            self.config.llm.budget = budget
        if api_key:
            self.config.llm.api_key = api_key

        # Set multi-agent mode
        self.config.orchestrator.use_multi_agent = multi_agent

        # Set tool logging configuration
        self.config.orchestrator.log_tool_calls = log_tool_calls
        self.config.orchestrator.tool_log_file = tool_log_file

        # Set debug mode
        self.config.orchestrator.debug = debug

        self._orchestrator: Optional[AgentOrchestrator] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._orchestrator = AgentOrchestrator(
            self.config,
            str(self.repo_path),
            model=self._model_override,
            supervisor_model=self._supervisor_model_override,
            worker_model=self._worker_model_override,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._orchestrator:
            await self._orchestrator.close()

    async def chat(self, message: str, session_id: Optional[str] = None) -> str:
        """
        Send a message to EQUITR Coder and get a response.

        Args:
            message: The message to send
            session_id: Optional session ID for conversation continuity

        Returns:
            The agent's response
        """
        if not self._orchestrator:
            raise RuntimeError("API must be used as async context manager")

        result = await self._orchestrator.run(message, session_id)
        # Return just the content string, not the full dictionary
        return result.get("content", str(result))

    def create_todo(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: Optional[str] = None,
        tags: Optional[List[str]] = None,
        assignee: Optional[str] = None,
    ) -> TodoItem:
        """
        Create a new todo item.

        Args:
            title: Title of the todo
            description: Detailed description
            priority: Priority level (low, medium, high, urgent)
            due_date: Due date in ISO format (YYYY-MM-DD)
            tags: List of tags for categorization
            assignee: Person assigned to this todo

        Returns:
            The created TodoItem
        """
        return todo_manager.create_todo(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags or [],
            assignee=assignee,
        )

    def update_todo(self, todo_id: str, **kwargs) -> Optional[TodoItem]:
        """
        Update an existing todo item.

        Args:
            todo_id: ID of the todo to update
            **kwargs: Fields to update (title, description, status, priority, etc.)

        Returns:
            The updated TodoItem or None if not found
        """
        return todo_manager.update_todo(todo_id, **kwargs)

    def delete_todo(self, todo_id: str) -> bool:
        """
        Delete a todo item.

        Args:
            todo_id: ID of the todo to delete

        Returns:
            True if deleted, False if not found
        """
        return todo_manager.delete_todo(todo_id)

    def list_todos(self, **filters) -> List[TodoItem]:
        """
        List todos with optional filters.

        Args:
            **filters: Optional filters (status, priority, assignee, tag)

        Returns:
            List of TodoItems matching the filters
        """
        return todo_manager.list_todos(**filters)

    def get_todo(self, todo_id: str) -> Optional[TodoItem]:
        """
        Get a specific todo by ID.

        Args:
            todo_id: ID of the todo

        Returns:
            The TodoItem or None if not found
        """
        return todo_manager.get_todo(todo_id)

    @property
    def session_history(self) -> List[Dict[str, Any]]:
        """Get the current session history."""
        if not self._orchestrator:
            return []

        messages = self._orchestrator.session_manager.get_messages()
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    @property
    def total_cost(self) -> float:
        """Get the total cost of the current session."""
        if not self._orchestrator:
            return 0.0
        return self._orchestrator.total_cost

    @property
    def iteration_count(self) -> int:
        """Get the number of iterations in the current session."""
        if not self._orchestrator:
            return 0
        return self._orchestrator.iteration_count

    def get_tool_call_logs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get tool call logs from the current session."""
        if not self._orchestrator:
            return []

        from dataclasses import asdict

        # Use the orchestrator's tool logger instance
        tool_logger = self._orchestrator.tool_logger
        logs = tool_logger.get_logs(limit=limit)
        return [asdict(log) for log in logs]

    def get_tool_call_stats(self) -> Dict[str, Any]:
        """Get statistics about tool calls in the current session."""
        if not self._orchestrator:
            return {}

        # Use the orchestrator's tool logger instance
        tool_logger = self._orchestrator.tool_logger
        return tool_logger.get_stats()

    def export_tool_logs(self, file_path: str, format: str = "json"):
        """Export tool call logs to a file."""
        if not self._orchestrator:
            return

        # Use the orchestrator's tool logger instance
        tool_logger = self._orchestrator.tool_logger
        tool_logger.export_logs(file_path, format)


class SyncEquitrAPI:
    """
    Synchronous wrapper for EquitrAPI.

    Provides a synchronous interface for simpler usage patterns.
    """

    def __init__(self, **kwargs):
        """Initialize with same arguments as EquitrAPI."""
        self._api_kwargs = kwargs
        self._loop = None

    def __enter__(self):
        """Context manager entry."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._api = EquitrAPI(**self._api_kwargs)
        self._loop.run_until_complete(self._api.__aenter__())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._api:
            self._loop.run_until_complete(
                self._api.__aexit__(exc_type, exc_val, exc_tb)
            )
        if self._loop:
            self._loop.close()

    def chat(self, message: str, session_id: Optional[str] = None) -> str:
        """Synchronous chat method."""
        return self._loop.run_until_complete(self._api.chat(message, session_id))

    def create_todo(self, **kwargs) -> TodoItem:
        """Create a todo item."""
        return self._api.create_todo(**kwargs)

    def update_todo(self, todo_id: str, **kwargs) -> Optional[TodoItem]:
        """Update a todo item."""
        return self._api.update_todo(todo_id, **kwargs)

    def delete_todo(self, todo_id: str) -> bool:
        """Delete a todo item."""
        return self._api.delete_todo(todo_id)

    def list_todos(self, **filters) -> List[TodoItem]:
        """List todos."""
        return self._api.list_todos(**filters)

    def get_todo(self, todo_id: str) -> Optional[TodoItem]:
        """Get a todo by ID."""
        return self._api.get_todo(todo_id)

    @property
    def session_history(self) -> List[Dict[str, Any]]:
        """Get session history."""
        return self._api.session_history

    @property
    def total_cost(self) -> float:
        """Get total cost."""
        return self._api.total_cost

    @property
    def iteration_count(self) -> int:
        """Get iteration count."""
        return self._api.iteration_count

    def get_tool_call_logs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get tool call logs."""
        return self._api.get_tool_call_logs(limit)

    def get_tool_call_stats(self) -> Dict[str, Any]:
        """Get tool call statistics."""
        return self._api.get_tool_call_stats()

    def export_tool_logs(self, file_path: str, format: str = "json"):
        """Export tool call logs to a file."""
        self._api.export_tool_logs(file_path, format)


# Convenience functions for quick usage
async def quick_chat(
    message: str,
    repo_path: str = ".",
    model: str = "anthropic/claude-3-haiku",
    api_key: Optional[str] = None,
) -> str:
    """
    Quick chat function for one-off interactions.

    Args:
        message: Message to send
        repo_path: Repository path
        model: Model to use
        api_key: API key if not in environment

    Returns:
        Agent response
    """
    async with EquitrAPI(repo_path=repo_path, model=model, api_key=api_key) as api:
        return await api.chat(message)


def sync_quick_chat(
    message: str,
    repo_path: str = ".",
    model: str = "anthropic/claude-3-haiku",
    api_key: Optional[str] = None,
) -> str:
    """
    Synchronous version of quick_chat.

    Args:
        message: Message to send
        repo_path: Repository path
        model: Model to use
        api_key: API key if not in environment

    Returns:
        Agent response
    """
    with SyncEquitrAPI(repo_path=repo_path, model=model, api_key=api_key) as api:
        return api.chat(message)


def create_project(
    repo_path: str = ".",
    profile: str = "default",
    model: str = "anthropic/claude-3-haiku",
    supervisor_model: Optional[str] = None,
    worker_model: Optional[str] = None,
    api_key: Optional[str] = None,
    budget: Optional[float] = None,
    error_logging: bool = False,
    project_type: str = "mario game",
    multi_agent: bool = False,
    log_tool_calls: bool = False,
) -> None:
    """
    Create complete project with documentation and implementation.

    Args:
        repo_path: Path to the repository
        profile: Configuration profile to use
        model: LLM model to use
        supervisor_model: Model for supervisor in multi-agent mode
        worker_model: Model for workers in multi-agent mode
        api_key: OpenRouter API key if not in environment
        budget: Budget limit in USD
        error_logging: Enable detailed error logging for debugging
        project_type: Type of project to create (default: mario game)
        multi_agent: Enable multi-agent mode
        log_tool_calls: Enable tool call logging
    """
    try:
        with SyncEquitrAPI(
            repo_path=repo_path,
            profile=profile,
            model=model,
            supervisor_model=supervisor_model,
            worker_model=worker_model,
            budget=budget,
            api_key=api_key,  # Pass api_key to init for standardized handling
            multi_agent=multi_agent,
            log_tool_calls=log_tool_calls,
        ) as api:
            print(f"🚀 Starting {project_type} project creation...")

            # Create comprehensive documentation
            print("📋 Creating requirements documentation...")
            api.chat(
                f"Create comprehensive requirements documentation (requirements.md) for a {project_type} including: project overview, functional requirements, non-functional requirements, user stories, acceptance criteria, and success metrics"
            )

            print("🏗️  Creating system documentation...")
            api.chat(
                f"Create system documentation (system.md) for a {project_type} including: system architecture, component overview, data flow, API design, technical specifications, and security considerations"
            )

            print("📝 Creating project todo list...")
            api.chat(
                f"Create project todo list with all tasks needed to build a complete {project_type}: setup development environment, create game engine, implement player mechanics, add levels, create assets, add sound, testing, and deployment"
            )

            print("🎮 Implementing complete {project_type}...")
            # Implement the complete project
            api.chat(
                f"Implement the complete {project_type} based on the requirements and system design. Create all necessary files including: main game file, player character, level system, collision detection, graphics rendering, sound system, game states (menu, playing, game over), scoring system, and ensure the game is fully playable. Use pygame for the game engine."
            )

            print("✅ Project creation completed!")

            # Show tool call statistics if logging was enabled
            if log_tool_calls:
                stats = api.get_tool_call_stats()
                if stats:
                    print(f"\n📊 Tool Call Statistics:")
                    print(f"  Total calls: {stats.get('total_calls', 0)}")
                    print(f"  Success rate: {stats.get('success_rate', 0):.1%}")
                    print(
                        f"  Total duration: {stats.get('total_duration_ms', 0):.1f}ms"
                    )

    except Exception as e:
        if error_logging:
            import traceback

            print(f"❌ Error in create_project: {str(e)}")
            print(traceback.format_exc())
        else:
            print(f"❌ Error: {str(e)}")
