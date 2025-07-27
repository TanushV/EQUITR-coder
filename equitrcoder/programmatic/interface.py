"""
Clean OOP Programmatic Interface for EQUITR Coder

This module provides a high-level, object-oriented interface for using EQUITR Coder
programmatically. It follows standard Python design patterns and conventions.
"""

import asyncio
from typing import Optional, List, Dict, Any, Callable, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import os
import litellm

from ..agents.base_agent import BaseAgent
from ..agents.worker_agent import WorkerAgent
from ..orchestrators.single_orchestrator import SingleAgentOrchestrator
from ..orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator, WorkerConfig, TaskResult
from ..core.session import SessionManagerV2, SessionData
from ..core.config import Config, config_manager
from ..tools.discovery import discover_tools
from ..utils.git_manager import GitManager
from ..providers.litellm import LiteLLMProvider


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
        git_enabled: bool = True
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
        
        # Initialize orchestrators
        self._single_orchestrator: Optional[SingleAgentOrchestrator] = None
        self._multi_orchestrator: Optional[MultiAgentOrchestrator] = None
        
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
            "aws": bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")),
            "cohere": bool(os.getenv("COHERE_API_KEY")),
            # Add more providers as needed
        }
        return {provider: available for provider, available in providers.items() if available}
    
    async def check_model_availability(self, model: str, test_call: bool = False) -> bool:
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
                    max_tokens=1
                )
                return bool(response and response.choices)
            return True
        except Exception:
            return False
    
    async def execute_task(
        self,
        task_description: str,
        config: Optional[Union[TaskConfiguration, MultiAgentTaskConfiguration]] = None
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
            if result.success and config and getattr(config, 'auto_commit', True) and self.git_enabled:
                commit_msg = getattr(config, 'commit_message', None) or f"Complete task: {task_description}"
                if self.git_manager.commit_task_completion(commit_msg):
                    result.git_committed = True
                    # Get the commit hash
                    recent_commits = self.git_manager.get_recent_commits(1)
                    if recent_commits:
                        result.commit_hash = recent_commits[0]['hash']
            
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
                error=str(e)
            )
            
            if self.on_task_complete:
                self.on_task_complete(error_result)
            
            return error_result
    
    async def _execute_single_task(
        self,
        task_description: str,
        config: Optional[TaskConfiguration]
    ) -> ExecutionResult:
        """Execute task in single-agent mode with mandatory 3-document creation."""
        if not config:
            config = TaskConfiguration(description=task_description)
        
        try:
            # MANDATORY: Create the 3 documents first (automatic for programmatic mode)
            from ..core.document_workflow import DocumentWorkflowManager
            
            doc_manager = DocumentWorkflowManager(model=config.model or "moonshot/kimi-k2-0711-preview")
            
            # Create documents automatically (no user interaction in programmatic mode)
            doc_result = await doc_manager.create_documents_programmatic(
                user_prompt=task_description,
                project_path=str(self.repo_path)
            )
            
            if not doc_result.success:
                return ExecutionResult(
                    success=False,
                    content="",
                    cost=0.0,
                    iterations=0,
                    session_id="error",
                    execution_time=0.0,
                    error=f"Failed to create planning documents: {doc_result.error}"
                )
            
            # Create agent
            agent = BaseAgent(
                max_cost=config.max_cost,
                max_iterations=config.max_iterations
            )
            
            # Set callbacks
            if self.on_tool_call:
                agent.on_tool_call_callback = self.on_tool_call
            
            # Create orchestrator
            if not self._single_orchestrator:
                self._single_orchestrator = SingleAgentOrchestrator(
                    agent=agent,
                    session_manager=self.session_manager,
                    model=config.model or "moonshot/kimi-k2-0711-preview"
                )
            
            # Set callbacks
            if self.on_message:
                self._single_orchestrator.set_callbacks(on_message=self.on_message)
            
            # Enhanced task description with document context
            enhanced_task = f"""
Original task: {task_description}

You have access to the following planning documents that were automatically created:
- Requirements: {doc_result.requirements_path}
- Design: {doc_result.design_path}  
- Todos: {doc_result.todos_path}

Please read these documents first, then execute the task according to the plan.
Focus on completing the todos one by one, following the design specifications.
"""
            
            # Execute task
            result = await self._single_orchestrator.execute_task(
                task_description=enhanced_task,
                session_id=config.session_id
            )
            
            return ExecutionResult(
                success=result["success"],
                content=result.get("content", ""),
                cost=result.get("cost", 0.0),
                iterations=result.get("iterations", 0),
                session_id=result.get("session_id", ""),
                execution_time=0.0,  # Will be set by caller
                error=result.get("error")
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                content="",
                cost=0.0,
                iterations=0,
                session_id="error",
                execution_time=0.0,
                error=str(e)
            )
    
    async def _execute_multi_task(
        self,
        task_description: str,
        config: Optional[MultiAgentTaskConfiguration]
    ) -> ExecutionResult:
        """Execute task in multi-agent mode with mandatory 3-document creation and split todos."""
        if not config:
            config = MultiAgentTaskConfiguration(description=task_description)
        
        try:
            # MANDATORY: Create the 3 documents first (automatic for programmatic mode)
            from ..core.document_workflow import DocumentWorkflowManager
            
            doc_manager = DocumentWorkflowManager(model=config.supervisor_model or "moonshot/kimi-k2-0711-preview")
            
            # Create shared requirements and design documents
            print("🔍 Creating shared requirements document...")
            requirements_content = await doc_manager._generate_requirements(task_description)
            requirements_path = Path(self.repo_path) / "docs" / "requirements.md"
            requirements_path.parent.mkdir(exist_ok=True)
            requirements_path.write_text(requirements_content)
            
            print("🏗️ Creating shared design document...")
            design_content = await doc_manager._generate_design(task_description, requirements_content)
            design_path = Path(self.repo_path) / "docs" / "design.md"
            design_path.write_text(design_content)
            
            # Create split todos for parallel agents
            print(f"📋 Creating split todos for {config.max_workers} agents...")
            agent_todo_files = await doc_manager.create_split_todos_for_parallel_agents(
                user_prompt=task_description,
                requirements_content=requirements_content,
                design_content=design_content,
                num_agents=config.max_workers,
                project_path=str(self.repo_path)
            )
            
            if not agent_todo_files:
                return ExecutionResult(
                    success=False,
                    content="",
                    cost=0.0,
                    iterations=0,
                    session_id="error",
                    execution_time=0.0,
                    error="Failed to create split todos for parallel agents"
                )
            
            # Create providers
            supervisor_provider = LiteLLMProvider(model=config.supervisor_model or "moonshot/kimi-k2-0711-preview")
            worker_provider = LiteLLMProvider(model=config.worker_model or "moonshot/kimi-k2-0711-preview")
            
            # Create orchestrator
            if not self._multi_orchestrator:
                self._multi_orchestrator = MultiAgentOrchestrator(
                    supervisor_provider=supervisor_provider,
                    worker_provider=worker_provider,
                    max_concurrent_workers=config.max_workers,
                    global_cost_limit=config.max_cost
                )
            
            # Create worker tasks with individual todo assignments
            worker_tasks = []
            for i, todo_file in enumerate(agent_todo_files):
                enhanced_task = f"""
Original task: {task_description}

You are Agent {i + 1} of {config.max_workers}.

You have access to the following planning documents:
- Requirements: {requirements_path}
- Design: {design_path}
- Your assigned todos: {todo_file}

CRITICAL INSTRUCTIONS:
1. Read the requirements.md and design.md files for context
2. Read your assigned todos file: {todo_file}
3. Complete ALL todos assigned to you
4. You cannot finish until ALL your todos are marked as completed
5. Use the update_todo tool to mark todos as completed when done
6. Work systematically through each todo
7. Follow the design specifications exactly

You are working in parallel with other agents. Focus only on your assigned todos.
"""
                
                worker_tasks.append({
                    "task_id": f"agent_{i + 1}_todos",
                    "worker_id": f"agent_{i + 1}",
                    "task_description": enhanced_task,
                    "context": {"agent_id": i + 1, "todo_file": todo_file}
                })
            
            # Execute coordination with split todos
            result = await self._multi_orchestrator.coordinate_workers(
                coordination_task=f"Multi-agent execution: {task_description}",
                worker_tasks=worker_tasks
            )
            
            return ExecutionResult(
                success=result["success"],
                content=result.get("content", ""),
                cost=result.get("total_cost", 0.0),
                iterations=len(result.get("worker_results", [])),
                session_id="multi_agent_session",
                execution_time=0.0,  # Will be set by caller
                error=result.get("error")
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                content="",
                cost=0.0,
                iterations=0,
                session_id="error",
                execution_time=0.0,
                error=str(e)
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
            max_iterations=config.max_iterations
        )
    
    async def execute_parallel_tasks(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[TaskResult]:
        """
        Execute multiple tasks in parallel using multi-agent mode.
        
        Args:
            tasks: List of task dictionaries with keys like task_id, worker_id, task_description
            
        Returns:
            List of TaskResult objects
        """
        if self.mode != "multi":
            raise ValueError("Parallel tasks require multi-agent mode")
        
        if not self._multi_orchestrator:
            raise ValueError("Multi-agent orchestrator not initialized")
        
        return await self._multi_orchestrator.execute_parallel_tasks(tasks)
    
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
        if self._multi_orchestrator:
            await self._multi_orchestrator.shutdown()


# Convenience factory functions
def create_single_agent_coder(
    repo_path: str = ".",
    model: Optional[str] = None,
    git_enabled: bool = True
) -> EquitrCoder:
    """
    Create a single-agent EQUITR Coder instance.
    
    Args:
        repo_path: Path to repository
        model: Model to use
        git_enabled: Whether to enable git operations
        
    Returns:
        EquitrCoder instance configured for single-agent mode
    """
    return EquitrCoder(
        mode="single",
        repo_path=repo_path,
        git_enabled=git_enabled
    )


def create_multi_agent_coder(
    repo_path: str = ".",
    max_workers: int = 3,
    supervisor_model: Optional[str] = None,
    worker_model: Optional[str] = None,
    git_enabled: bool = True
) -> EquitrCoder:
    """
    Create a multi-agent EQUITR Coder instance.
    
    Args:
        repo_path: Path to repository
        max_workers: Maximum number of concurrent workers
        supervisor_model: Model for supervisor agent
        worker_model: Model for worker agents
        git_enabled: Whether to enable git operations
        
    Returns:
        EquitrCoder instance configured for multi-agent mode
    """
    return EquitrCoder(
        mode="multi",
        repo_path=repo_path,
        git_enabled=git_enabled
    )


# Legacy alias for backward compatibility
EquitrCoderAPI = EquitrCoder 