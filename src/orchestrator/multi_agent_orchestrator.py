import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import importlib.util
import sys
from concurrent.futures import ThreadPoolExecutor

from src.core.project_checklist import get_checklist_manager, WorkerSpec, Task
from src.tools.ask_supervisor import create_ask_supervisor_tool
from src.config.model_config import get_config_manager


class WorkerAgent:
    def __init__(self, spec: WorkerSpec, project_root: str = "."):
        self.spec = spec
        self.project_root = Path(project_root)
        self.ask_supervisor = create_ask_supervisor_tool()
        self.allowed_files = set()
        self._setup_file_access()

    def _setup_file_access(self):
        """Setup file access based on scope_paths."""
        for scope_path in self.spec.scope_paths:
            full_path = self.project_root / scope_path
            if full_path.is_file():
                self.allowed_files.add(full_path.resolve())
            elif full_path.is_dir():
                for file_path in full_path.rglob("*"):
                    if file_path.is_file():
                        self.allowed_files.add(file_path.resolve())

    def can_access_file(self, file_path: str) -> bool:
        """Check if worker can access the given file."""
        resolved_path = Path(file_path).resolve()
        return resolved_path in self.allowed_files

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if worker can use the given tool."""
        return tool_name in self.spec.allowed_tools

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a task assigned to this worker."""
        if task.assigned_to != self.spec.id:
            return {"error": f"Task {task.id} not assigned to this worker"}

        # Create a restricted environment for the worker
        worker_env = {
            "__builtins__": __builtins__,
            "ask_supervisor": self.ask_supervisor,
            "project_root": str(self.project_root),
            "worker_id": self.spec.id,
            "task_id": task.id,
            "task_title": task.title,
        }

        # Import and execute task-specific code
        try:
            # This is a simplified version - in real implementation, you'd have
            # proper task execution with sandboxing
            result = await self._execute_task_logic(task, worker_env)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": str(e), "worker_id": self.spec.id, "task_id": task.id}

    async def _execute_task_logic(self, task: Task, env: Dict[str, Any]) -> Any:
        """Execute the actual task logic."""
        # This would be replaced with actual task execution
        return f"Task {task.id} executed by {self.spec.id}"


class MultiAgentOrchestrator:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.checklist_manager = get_checklist_manager(str(project_root))
        self.workers: Dict[str, WorkerAgent] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

    def initialize_workers(self):
        """Initialize workers based on the current checklist."""
        checklist = self.checklist_manager.get_checklist()

        for worker_spec in checklist.workers_spec:
            if worker_spec.id not in self.workers:
                self.workers[worker_spec.id] = WorkerAgent(
                    worker_spec, str(self.project_root)
                )

    async def run_tasks(self) -> Dict[str, Any]:
        """Run all pending tasks using the configured workers."""
        self.initialize_workers()

        pending_tasks = self.checklist_manager.get_pending_tasks()
        if not pending_tasks:
            return {"message": "No pending tasks", "tasks_completed": 0}

        results = []

        for task in pending_tasks:
            worker = self.workers.get(task.assigned_to)
            if not worker:
                results.append(
                    {
                        "task_id": task.id,
                        "error": f"No worker found for task assignment: {task.assigned_to}",
                    }
                )
                continue

            # Mark task as in progress
            self.checklist_manager.update_task_status(task.id, "in_progress")

            # Execute task
            result = await worker.execute_task(task)

            if "success" in result:
                self.checklist_manager.update_task_status(task.id, "done")
            else:
                self.checklist_manager.update_task_status(task.id, "todo")

            results.append(
                {"task_id": task.id, "worker_id": task.assigned_to, **result}
            )

        return {
            "tasks_completed": len([r for r in results if "success" in r]),
            "tasks_failed": len([r for r in results if "error" in r]),
            "results": results,
        }

    def get_worker_status(self) -> Dict[str, Any]:
        """Get status of all workers."""
        return {
            worker_id: {
                "spec": asdict(worker.spec),
                "allowed_files": len(worker.allowed_files),
                "allowed_tools": worker.spec.allowed_tools,
            }
            for worker_id, worker in self.workers.items()
        }

    def get_task_status(self) -> Dict[str, Any]:
        """Get status of all tasks."""
        return {
            "pending": len(self.checklist_manager.get_pending_tasks()),
            "in_progress": len(self.checklist_manager.get_in_progress_tasks()),
            "completed": len(self.checklist_manager.get_completed_tasks()),
            "total": len(self.checklist_manager.get_checklist().tasks),
        }


# Global orchestrator instance
_orchestrator = None


def get_orchestrator(project_root: str = ".") -> MultiAgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator(project_root)
    return _orchestrator


async def run_multi_agent_workflow(project_root: str = ".") -> Dict[str, Any]:
    """Convenience function to run the multi-agent workflow."""
    orchestrator = get_orchestrator(project_root)
    return await orchestrator.run_tasks()
