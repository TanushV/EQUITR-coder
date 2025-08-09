"""Task management for multi-agent systems."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    """Individual task in a multi-agent system."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = Field(..., description="What needs to be done")
    status: Literal["todo", "in_progress", "done", "failed"] = "todo"
    files: List[str] = Field(
        default_factory=list, description="Files this task should focus on"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="Task IDs this task depends on"
    )
    assigned_agent: Optional[str] = None
    priority: int = Field(
        default=5, description="Priority 1-10, higher is more important"
    )
    estimated_duration: Optional[int] = None  # minutes
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def update_status(
        self,
        new_status: Literal["todo", "in_progress", "done", "failed"],
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update task status and timestamps."""
        self.status = new_status
        self.updated_at = datetime.now()

        if new_status == "in_progress" and self.started_at is None:
            self.started_at = datetime.now()
        elif new_status in ["done", "failed"]:
            self.completed_at = datetime.now()

        if result:
            self.result = result
        if error:
            self.error = error

    def is_ready(self, completed_tasks: List[str]) -> bool:
        """Check if task is ready to be executed (all dependencies completed)."""
        if self.status != "todo":
            return False
        return all(dep_id in completed_tasks for dep_id in self.dependencies)

    def duration_minutes(self) -> Optional[int]:
        """Calculate actual duration in minutes if task is completed."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() / 60)
        return None


class TaskList(BaseModel):
    """Collection of tasks with management methods."""

    tasks: List[Task] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def add_task(self, task: Task) -> str:
        """Add a task to the list."""
        self.tasks.append(task)
        self.updated_at = datetime.now()
        return task.id

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def update_task_status(
        self,
        task_id: str,
        status: Literal["todo", "in_progress", "done", "failed"],
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Update task status."""
        task = self.get_task(task_id)
        if task:
            task.update_status(status, result, error)
            self.updated_at = datetime.now()
            return True
        return False

    def get_ready_tasks(self) -> List[Task]:
        """Get all tasks that are ready to be executed."""
        completed_task_ids = [t.id for t in self.tasks if t.status == "done"]
        return [task for task in self.tasks if task.is_ready(completed_task_ids)]

    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get all tasks with a specific status."""
        return [task for task in self.tasks if task.status == status]

    def get_tasks_by_agent(self, agent_name: str) -> List[Task]:
        """Get all tasks assigned to a specific agent."""
        return [task for task in self.tasks if task.assigned_agent == agent_name]

    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        return all(task.status in ["done", "failed"] for task in self.tasks)

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of task progress."""
        total = len(self.tasks)
        if total == 0:
            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "todo": 0,
                "failed": 0,
                "progress": 0.0,
            }

        status_counts = {}
        for status in ["todo", "in_progress", "done", "failed"]:
            status_counts[status] = len(self.get_tasks_by_status(status))

        return {
            "total": total,
            "completed": status_counts["done"],
            "in_progress": status_counts["in_progress"],
            "todo": status_counts["todo"],
            "failed": status_counts["failed"],
            "progress": status_counts["done"] / total * 100,
        }

    def get_next_task(self, agent_name: Optional[str] = None) -> Optional[Task]:
        """Get the next task to be executed, optionally filtered by agent."""
        ready_tasks = self.get_ready_tasks()

        if agent_name:
            ready_tasks = [
                t
                for t in ready_tasks
                if t.assigned_agent == agent_name or t.assigned_agent is None
            ]

        if not ready_tasks:
            return None

        # Sort by priority (higher first), then by created_at
        ready_tasks.sort(key=lambda t: (-t.priority, t.created_at))
        return ready_tasks[0]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "tasks": [task.model_dump() for task in self.tasks],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "summary": self.get_progress_summary(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskList":
        """Create TaskList from dictionary."""
        tasks = [Task(**task_data) for task_data in data.get("tasks", [])]
        return cls(
            tasks=tasks,
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now().isoformat())
            ),
            updated_at=datetime.fromisoformat(
                data.get("updated_at", datetime.now().isoformat())
            ),
        )
