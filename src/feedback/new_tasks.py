import json
from typing import Dict, Any, List
from pathlib import Path

from src.core.project_checklist import get_checklist_manager, Task


class NewTasksGenerator:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.checklist_manager = get_checklist_manager(str(project_root))

    def process_audit_feedback(
        self, audit_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process audit feedback and generate new tasks."""
        new_tasks = []

        # Generate tasks based on audit failures
        if not audit_results.get("audit_passed", False):
            new_tasks.extend(self._generate_test_tasks(audit_results))
            new_tasks.extend(self._generate_lint_tasks(audit_results))
            new_tasks.extend(self._generate_git_tasks(audit_results))
            new_tasks.extend(self._generate_dependency_tasks(audit_results))
            new_tasks.extend(self._generate_structure_tasks(audit_results))

        # Add tasks to checklist
        if new_tasks:
            self._add_tasks_to_checklist(new_tasks)

        return new_tasks

    def _generate_test_tasks(
        self, audit_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate tasks for test failures."""
        tasks = []

        test_results = audit_results.get("tests", {})
        if not test_results.get("passed", True):
            if test_results.get("tests_found", False):
                tasks.append(
                    {
                        "id": self._get_next_task_id(),
                        "title": "Fix failing tests",
                        "assigned_to": "test-worker",
                        "status": "todo",
                        "priority": "high",
                        "description": "Address failing test cases identified in audit",
                    }
                )
            else:
                tasks.append(
                    {
                        "id": self._get_next_task_id(),
                        "title": "Add comprehensive tests",
                        "assigned_to": "test-worker",
                        "status": "todo",
                        "priority": "high",
                        "description": "Create test suite for the project",
                    }
                )

        return tasks

    def _generate_lint_tasks(
        self, audit_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate tasks for linting issues."""
        tasks = []

        lint_results = audit_results.get("linting", {})
        if not lint_results.get("passed", True):
            tasks.append(
                {
                    "id": self._get_next_task_id(),
                    "title": "Fix code style issues",
                    "assigned_to": "lint-worker",
                    "status": "todo",
                    "priority": "medium",
                    "description": "Address linting and code style issues",
                }
            )

        return tasks

    def _generate_git_tasks(
        self, audit_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate tasks for git issues."""
        tasks = []

        git_results = audit_results.get("git_status", {})
        if git_results.get("git_repo", False) and not git_results.get("clean", True):
            tasks.append(
                {
                    "id": self._get_next_task_id(),
                    "title": "Commit pending changes",
                    "assigned_to": "git-worker",
                    "status": "todo",
                    "priority": "medium",
                    "description": "Commit uncommitted changes to git",
                }
            )
        elif not git_results.get("git_repo", False):
            tasks.append(
                {
                    "id": self._get_next_task_id(),
                    "title": "Initialize git repository",
                    "assigned_to": "git-worker",
                    "status": "todo",
                    "priority": "low",
                    "description": "Initialize git repository for version control",
                }
            )

        return tasks

    def _generate_dependency_tasks(
        self, audit_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate tasks for dependency issues."""
        tasks = []

        dep_results = audit_results.get("dependencies", {})
        if not dep_results.get("has_requirements", False):
            tasks.append(
                {
                    "id": self._get_next_task_id(),
                    "title": "Create dependency specification",
                    "assigned_to": "config-worker",
                    "status": "todo",
                    "priority": "medium",
                    "description": "Create requirements.txt or pyproject.toml for dependencies",
                }
            )

        return tasks

    def _generate_structure_tasks(
        self, audit_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate tasks for project structure issues."""
        tasks = []

        structure = audit_results.get("file_structure", {})

        if structure.get("python_files", 0) == 0:
            tasks.append(
                {
                    "id": self._get_next_task_id(),
                    "title": "Create project structure",
                    "assigned_to": "structure-worker",
                    "status": "todo",
                    "priority": "high",
                    "description": "Set up basic project structure with Python files",
                }
            )

        if structure.get("test_files", 0) == 0:
            tasks.append(
                {
                    "id": self._get_next_task_id(),
                    "title": "Create test directory structure",
                    "assigned_to": "test-worker",
                    "status": "todo",
                    "priority": "medium",
                    "description": "Set up test directory and initial test files",
                }
            )

        return tasks

    def _get_next_task_id(self) -> int:
        """Get the next available task ID."""
        checklist = self.checklist_manager.get_checklist()
        if not checklist.tasks:
            return 1
        return max(task.id for task in checklist.tasks) + 1

    def _add_tasks_to_checklist(self, new_tasks: List[Dict[str, Any]]):
        """Add new tasks to the project checklist."""
        for task_data in new_tasks:
            task = Task(
                id=task_data["id"],
                title=task_data["title"],
                assigned_to=task_data["assigned_to"],
                status=task_data["status"],
            )
            self.checklist_manager.add_task(task)

    def get_feedback_summary(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of feedback for display."""
        new_tasks = self.process_audit_feedback(audit_results)

        return {
            "audit_passed": audit_results.get("audit_passed", False),
            "new_tasks_generated": len(new_tasks),
            "tasks_by_category": self._categorize_tasks(new_tasks),
            "next_steps": self._get_next_steps(new_tasks),
        }

    def _categorize_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize tasks by type."""
        categories = {}
        for task in tasks:
            category = task.get("assigned_to", "unknown").split("-")[0]
            categories[category] = categories.get(category, 0) + 1
        return categories

    def _get_next_steps(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Get recommended next steps."""
        if not tasks:
            return ["All tasks completed successfully!"]

        steps = []
        high_priority = [t for t in tasks if t.get("priority") == "high"]

        if high_priority:
            steps.append(f"Address {len(high_priority)} high priority tasks first")

        steps.append("Run multi-agent workflow to process new tasks")
        steps.append("Re-run audit after completing new tasks")

        return steps


def process_audit_feedback(
    audit_results: Dict[str, Any], project_root: str = "."
) -> List[Dict[str, Any]]:
    """Convenience function to process audit feedback."""
    generator = NewTasksGenerator(project_root)
    return generator.process_audit_feedback(audit_results)


def get_feedback_summary(
    audit_results: Dict[str, Any], project_root: str = "."
) -> Dict[str, Any]:
    """Get feedback summary."""
    generator = NewTasksGenerator(project_root)
    return generator.get_feedback_summary(audit_results)
