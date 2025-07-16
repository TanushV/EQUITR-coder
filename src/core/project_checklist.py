import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class WorkerSpec:
    id: str
    scope_paths: List[str]
    description: str
    allowed_tools: List[str]


@dataclass
class Task:
    id: int
    title: str
    assigned_to: str
    status: str  # "todo", "in_progress", "done", "cancelled"


@dataclass
class ProjectChecklist:
    workers_spec: List[WorkerSpec]
    tasks: List[Task]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workers_spec": [asdict(w) for w in self.workers_spec],
            "tasks": [asdict(t) for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectChecklist":
        workers = [WorkerSpec(**w) for w in data.get("workers_spec", [])]
        tasks = [Task(**t) for t in data.get("tasks", [])]
        return cls(workers_spec=workers, tasks=tasks)


class ChecklistManager:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.checklist_file = self.project_root / "PROJECT_CHECKLIST.json"
        self._checklist = self._load_checklist()

    def _load_checklist(self) -> ProjectChecklist:
        if self.checklist_file.exists():
            try:
                with open(self.checklist_file, "r") as f:
                    data = json.load(f)
                return ProjectChecklist.from_dict(data)
            except (json.JSONDecodeError, TypeError):
                pass

        # Return empty checklist if file doesn't exist or is invalid
        return ProjectChecklist(workers_spec=[], tasks=[])

    def save_checklist(self):
        self.checklist_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checklist_file, "w") as f:
            json.dump(self._checklist.to_dict(), f, indent=2)

    def get_checklist(self) -> ProjectChecklist:
        return self._checklist

    def add_worker_spec(self, worker_spec: WorkerSpec):
        self._checklist.workers_spec.append(worker_spec)
        self.save_checklist()

    def add_task(self, task: Task):
        self._checklist.tasks.append(task)
        self.save_checklist()

    def update_task_status(self, task_id: int, status: str):
        for task in self._checklist.tasks:
            if task.id == task_id:
                task.status = status
                self.save_checklist()
                return True
        return False

    def get_tasks_by_worker(self, worker_id: str) -> List[Task]:
        return [t for t in self._checklist.tasks if t.assigned_to == worker_id]

    def get_pending_tasks(self) -> List[Task]:
        return [t for t in self._checklist.tasks if t.status == "todo"]

    def get_in_progress_tasks(self) -> List[Task]:
        return [t for t in self._checklist.tasks if t.status == "in_progress"]

    def get_completed_tasks(self) -> List[Task]:
        return [t for t in self._checklist.tasks if t.status == "done"]

    def all_tasks_completed(self) -> bool:
        return all(t.status == "done" for t in self._checklist.tasks)

    def clear_checklist(self):
        self._checklist = ProjectChecklist(workers_spec=[], tasks=[])
        self.save_checklist()


# Global instance
_checklist_manager = None


def get_checklist_manager(project_root: str = ".") -> ChecklistManager:
    global _checklist_manager
    if _checklist_manager is None:
        _checklist_manager = ChecklistManager(project_root)
    return _checklist_manager
