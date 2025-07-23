"""
Enhanced Multi-Agent Orchestrator with robust features from core orchestrator.
"""
import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from ..agents.worker_agent import WorkerAgent
from ..agents.base_agent import BaseAgent
from ..core.session import SessionManagerV2, SessionData
from ..core.context_manager import ContextManager
from ..core.supervisor import SupervisorAgent
from ..repository.indexer import RepositoryIndexer
from ..tools.builtin.ask_supervisor import AskSupervisor
from ..providers.openrouter import OpenRouterProvider, Message
from ..providers.litellm import LiteLLMProvider


@dataclass
class TaskResult:
    """Result of a multi-agent task."""
    task_id: str
    worker_id: str
    success: bool
    result: Any = None
    error: str = None
    execution_time: float = 0.0
    cost: float = 0.0
    tokens_used: int = 0
    iteration_count: int = 0


@dataclass
class WorkerConfig:
    """Configuration for a worker agent."""
    worker_id: str
    scope_paths: List[str]
    allowed_tools: List[str]
    max_cost: Optional[float] = None
    max_iterations: Optional[int] = None


class MultiAgentOrchestrator:
    """Enhanced orchestrator for coordinating multiple worker agents with robust features."""

    def __init__(
        self,
        supervisor_provider: Optional[OpenRouterProvider] = None,
        worker_provider: Optional[OpenRouterProvider] = None,
        session_manager: Optional[SessionManagerV2] = None,
        repo_path: str = ".",
        max_concurrent_workers: int = 3,
        global_cost_limit: float = 10.0,
        max_total_iterations: int = 100,
        context_max_tokens: int = 8000
    ):
        self.supervisor_provider = supervisor_provider
        self.worker_provider = worker_provider
        self.repo_path = Path(repo_path)
        self.max_concurrent_workers = max_concurrent_workers
        self.global_cost_limit = global_cost_limit
        self.max_total_iterations = max_total_iterations
        
        # Initialize session management
        self.session_manager = session_manager or SessionManagerV2()
        
        # Initialize context management
        self.context_manager = ContextManager(
            max_tokens=context_max_tokens,
            model=getattr(supervisor_provider, "model", "gpt-4") if supervisor_provider else "gpt-4"
        )
        
        # Initialize repository indexer
        self.repo_indexer = RepositoryIndexer(repo_path=str(self.repo_path))
        
        # Initialize supervisor if provider available
        self.supervisor = None
        if supervisor_provider:
            self.supervisor = SupervisorAgent(
                supervisor_provider,
                self.session_manager,
                str(self.repo_path),
                use_multi_agent=True,
                worker_provider=worker_provider
            )

        # Runtime state
        self.workers: Dict[str, WorkerAgent] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: List[TaskResult] = []
        self.total_cost = 0.0
        self.total_iterations = 0
        
        # Callbacks
        self.on_task_start_callback: Optional[Callable] = None
        self.on_task_complete_callback: Optional[Callable] = None
        self.on_worker_message_callback: Optional[Callable] = None
        self.on_cost_update_callback: Optional[Callable] = None

    def create_worker(
        self,
        config: WorkerConfig,
        provider: Optional[OpenRouterProvider] = None
    ) -> WorkerAgent:
        """Create and register a new worker agent."""
        worker_provider = provider or self.worker_provider
        
        worker = WorkerAgent(
            worker_id=config.worker_id,
            scope_paths=config.scope_paths,
            allowed_tools=config.allowed_tools,
            project_root=str(self.repo_path),
            provider=worker_provider,
            max_cost=config.max_cost,
            max_iterations=config.max_iterations
        )

        # Set up callbacks
        if self.on_worker_message_callback:
            worker.on_message_callback = self.on_worker_message_callback
        
        if self.on_cost_update_callback:
            worker.on_cost_update_callback = self._handle_worker_cost_update

        self.workers[config.worker_id] = worker
        return worker

    def _handle_worker_cost_update(self, total_cost: float, delta: float):
        """Handle cost updates from workers."""
        self.total_cost += delta
        if self.on_cost_update_callback:
            self.on_cost_update_callback(self.total_cost, delta)

    async def execute_task(
        self,
        task_id: str,
        worker_id: str,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> TaskResult:
        """Execute a task using a specific worker."""
        if worker_id not in self.workers:
            return TaskResult(
                task_id=task_id,
                worker_id=worker_id,
                success=False,
                error=f"Worker {worker_id} not found",
            )

        worker = self.workers[worker_id]
        start_time = time.time()
        start_cost = worker.current_cost

        # Call task start callback
        if self.on_task_start_callback:
            self.on_task_start_callback(task_id, worker_id, task_description)

        try:
            # Create or load session
            if session_id:
                session = self.session_manager.load_session(session_id)
                if not session:
                    session = self.session_manager.create_session(session_id)
            else:
                session = self.session_manager.create_session()
            
            worker.session = session

            # Check global limits
            if self.total_cost >= self.global_cost_limit:
                raise Exception(f"Global cost limit ({self.global_cost_limit}) exceeded")
            
            if self.total_iterations >= self.max_total_iterations:
                raise Exception(f"Global iteration limit ({self.max_total_iterations}) exceeded")

            # Add task context
            if context:
                worker.add_message("system", f"Task context: {json.dumps(context)}")
            
            # Add task message
            worker.add_message("user", task_description)

            # Execute task (simplified - in real implementation would involve LLM calls)
            result = await self._execute_worker_task(worker, task_description, context)
            
            # Update session
            session.cost += worker.current_cost - start_cost
            session.iteration_count = worker.iteration_count
            await self.session_manager._save_session_to_disk(session)

            execution_time = time.time() - start_time
            cost_delta = worker.current_cost - start_cost
            
            task_result = TaskResult(
                task_id=task_id,
                worker_id=worker_id,
                success=True,
                result=result,
                execution_time=execution_time,
                cost=cost_delta,
                tokens_used=result.get("tokens_used", 0) if isinstance(result, dict) else 0,
                iteration_count=worker.iteration_count
            )

            self.task_results.append(task_result)
            self.total_iterations += worker.iteration_count

            # Call task complete callback
            if self.on_task_complete_callback:
                self.on_task_complete_callback(task_result)

            return task_result

        except Exception as e:
            execution_time = time.time() - start_time
            cost_delta = worker.current_cost - start_cost
            
            task_result = TaskResult(
                task_id=task_id,
                worker_id=worker_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
                cost=cost_delta,
                iteration_count=worker.iteration_count
            )

            self.task_results.append(task_result)
            
            # Call task complete callback
            if self.on_task_complete_callback:
                self.on_task_complete_callback(task_result)

            return task_result

    async def _execute_worker_task(
        self,
        worker: WorkerAgent,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the actual task using the worker."""
        # This is a simplified implementation
        # In a real scenario, this would involve:
        # 1. LLM calls to understand the task
        # 2. Tool usage to complete the task
        # 3. Iteration until completion or limits reached
        
        iteration_results = []
        
        while True:
            # Check worker limits
            limits = worker.check_limits()
            if not limits["can_continue"]:
                break
            
            # Increment iteration
            worker.increment_iteration()
            
            # Simulate task processing
            iteration_result = {
                "iteration": worker.iteration_count,
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "message": f"Processed task: {task_description}",
                "worker_id": worker.agent_id
            }
            
            iteration_results.append(iteration_result)
            
            # Add completion message
            worker.add_message(
                "assistant",
                f"Completed iteration {worker.iteration_count}",
                {"iteration_result": iteration_result}
            )
            
            # For demo purposes, complete after one iteration
            break
        
        return {
            "task_description": task_description,
            "iterations": iteration_results,
            "total_iterations": len(iteration_results),
            "worker_status": worker.get_status(),
            "tokens_used": 100  # Mock value
        }

    async def execute_parallel_tasks(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[TaskResult]:
        """Execute multiple tasks in parallel with proper concurrency control."""
        # Limit concurrent tasks
        semaphore = asyncio.Semaphore(self.max_concurrent_workers)

        async def execute_with_semaphore(task_info):
            async with semaphore:
                return await self.execute_task(**task_info)

        # Execute tasks concurrently
        task_coroutines = [execute_with_semaphore(task) for task in tasks]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Handle exceptions
        task_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_results.append(
                    TaskResult(
                        task_id=tasks[i].get("task_id", f"task_{i}"),
                        worker_id=tasks[i].get("worker_id", "unknown"),
                        success=False,
                        error=str(result),
                    )
                )
            else:
                task_results.append(result)

        return task_results

    async def coordinate_workers(
        self,
        coordination_task: str,
        worker_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Coordinate multiple workers with supervisor oversight."""
        if not self.supervisor:
            # Fallback to simple parallel execution
            results = await self.execute_parallel_tasks(worker_tasks)
            return {
                "coordination_task": coordination_task,
                "worker_results": results,
                "success": all(r.success for r in results)
            }
        
        # Use supervisor for coordination
        try:
            # Execute worker tasks
            worker_results = await self.execute_parallel_tasks(worker_tasks)
            
            # Get supervisor analysis
            supervisor_context = {
                "coordination_task": coordination_task,
                "worker_results": [r.__dict__ for r in worker_results],
                "total_cost": self.total_cost,
                "total_iterations": self.total_iterations
            }
            
            # This would involve calling the supervisor to analyze results
            # For now, return a simple coordination result
            coordination_result = {
                "coordination_task": coordination_task,
                "worker_results": worker_results,
                "supervisor_analysis": "Tasks completed successfully",
                "success": all(r.success for r in worker_results),
                "total_cost": sum(r.cost for r in worker_results),
                "total_time": sum(r.execution_time for r in worker_results)
            }
            
            return coordination_result
            
        except Exception as e:
            return {
                "coordination_task": coordination_task,
                "success": False,
                "error": str(e),
                "worker_results": []
            }

    def get_worker_status(self, worker_id: str) -> Dict[str, Any]:
        """Get status of a specific worker."""
        if worker_id not in self.workers:
            return {"error": f"Worker {worker_id} not found"}

        worker = self.workers[worker_id]
        return worker.get_worker_status()

    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status."""
        successful_tasks = sum(1 for r in self.task_results if r.success)
        failed_tasks = len(self.task_results) - successful_tasks
        
        return {
            "orchestrator_type": "multi_agent",
            "total_workers": len(self.workers),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.task_results),
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "total_cost": self.total_cost,
            "cost_limit": self.global_cost_limit,
            "total_iterations": self.total_iterations,
            "iteration_limit": self.max_total_iterations,
            "max_concurrent_workers": self.max_concurrent_workers,
            "has_supervisor": self.supervisor is not None,
            "repo_path": str(self.repo_path)
        }

    def set_callbacks(
        self,
        on_task_start: Optional[Callable] = None,
        on_task_complete: Optional[Callable] = None,
        on_worker_message: Optional[Callable] = None,
        on_cost_update: Optional[Callable] = None
    ):
        """Set callback functions for monitoring."""
        self.on_task_start_callback = on_task_start
        self.on_task_complete_callback = on_task_complete
        self.on_worker_message_callback = on_worker_message
        self.on_cost_update_callback = on_cost_update

    async def shutdown(self):
        """Shutdown all workers and clean up resources."""
        # Cancel active tasks
        for task in self.active_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self.active_tasks:
            await asyncio.gather(
                *self.active_tasks.values(), return_exceptions=True
            )

        # Reset workers
        for worker in self.workers.values():
            worker.reset()

        # Clear state
        self.workers.clear()
        self.active_tasks.clear()
        
        # Save final session state
        if hasattr(self, 'session_manager'):
            await self.session_manager._flush_dirty_sessions()


# Global orchestrator instance for backward compatibility
_orchestrator = None


def get_orchestrator(project_root: str = ".") -> MultiAgentOrchestrator:
    """Get global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator(repo_path=project_root)
    return _orchestrator


async def run_multi_agent_workflow(project_root: str = ".") -> Dict[str, Any]:
    """Convenience function to run the multi-agent workflow."""
    orchestrator = get_orchestrator(project_root)
    # This would need to be implemented based on specific workflow requirements
    return {"message": "Multi-agent workflow completed", "orchestrator_status": orchestrator.get_orchestrator_status()}
