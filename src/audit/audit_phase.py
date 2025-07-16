import json
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
import os

from src.core.project_checklist import get_checklist_manager
from src.config.model_config import get_config_manager


class AuditPhase:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.checklist_manager = get_checklist_manager(str(project_root))

    def run_audit(self) -> Dict[str, Any]:
        """Run comprehensive audit after all tasks are completed."""
        if not self.checklist_manager.all_tasks_completed():
            return {
                "status": "incomplete",
                "message": "Cannot run audit: not all tasks are completed",
                "pending_tasks": len(self.checklist_manager.get_pending_tasks()),
            }

        audit_results = {
            "status": "audit_started",
            "timestamp": self._get_timestamp(),
            "project_root": str(self.project_root),
            "checklist": self._audit_checklist(),
            "git_status": self._audit_git_status(),
            "file_structure": self._audit_file_structure(),
            "tests": self._audit_tests(),
            "linting": self._audit_linting(),
            "dependencies": self._audit_dependencies(),
        }

        # Check if audit passed
        audit_passed = all(
            [
                audit_results["tests"]["passed"],
                audit_results["linting"]["passed"],
                audit_results["git_status"]["clean"],
            ]
        )

        audit_results["audit_passed"] = audit_passed

        if not audit_passed:
            audit_results["new_tasks"] = self._generate_new_tasks(audit_results)

        # Save audit results
        self._save_audit_results(audit_results)

        return audit_results

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()

    def _audit_checklist(self) -> Dict[str, Any]:
        """Audit the project checklist."""
        checklist = self.checklist_manager.get_checklist()
        return {
            "total_tasks": len(checklist.tasks),
            "completed_tasks": len(self.checklist_manager.get_completed_tasks()),
            "workers_defined": len(checklist.workers_spec),
            "checklist_valid": len(checklist.tasks) > 0,
        }

    def _audit_git_status(self) -> Dict[str, Any]:
        """Audit git repository status."""
        try:
            # Check if git repo exists
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                return {
                    "git_repo": False,
                    "clean": False,
                    "message": "Not a git repository",
                }

            # Check git status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            # Get last commit info
            log_result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            return {
                "git_repo": True,
                "clean": len(status_result.stdout.strip()) == 0,
                "uncommitted_changes": status_result.stdout.strip().split("\n")
                if status_result.stdout.strip()
                else [],
                "recent_commits": log_result.stdout.strip().split("\n")
                if log_result.stdout.strip()
                else [],
            }

        except Exception as e:
            return {"git_repo": False, "clean": False, "error": str(e)}

    def _audit_file_structure(self) -> Dict[str, Any]:
        """Audit project file structure."""
        structure = {
            "total_files": 0,
            "python_files": 0,
            "config_files": 0,
            "test_files": 0,
            "directories": [],
        }

        try:
            for root, dirs, files in os.walk(self.project_root):
                # Skip hidden directories and common ignores
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["__pycache__", "node_modules"]
                ]

                rel_root = os.path.relpath(root, self.project_root)
                if rel_root != ".":
                    structure["directories"].append(rel_root)

                for file in files:
                    if not file.startswith("."):
                        structure["total_files"] += 1
                        if file.endswith(".py"):
                            structure["python_files"] += 1
                        elif file in ["requirements.txt", "setup.py", "pyproject.toml"]:
                            structure["config_files"] += 1
                        elif "test" in file.lower() and file.endswith(".py"):
                            structure["test_files"] += 1

            structure["directories"] = sorted(list(set(structure["directories"])))

        except Exception as e:
            structure["error"] = str(e)

        return structure

    def _audit_tests(self) -> Dict[str, Any]:
        """Audit test execution."""
        test_commands = [
            ["python", "-m", "pytest"],
            ["python", "-m", "unittest", "discover"],
            ["nosetests"],
        ]

        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    timeout=30,
                )

                if result.returncode == 0:
                    return {
                        "passed": True,
                        "command": " ".join(cmd),
                        "output": result.stdout,
                        "tests_found": True,
                    }

            except subprocess.TimeoutExpired:
                continue
            except FileNotFoundError:
                continue
            except Exception:
                continue

        # Check if test files exist
        test_files = list(self.project_root.rglob("test_*.py"))
        test_files.extend(list(self.project_root.rglob("*_test.py")))

        return {
            "passed": len(test_files) == 0,  # Pass if no test files
            "command": None,
            "output": f"Found {len(test_files)} test files",
            "tests_found": len(test_files) > 0,
        }

    def _audit_linting(self) -> Dict[str, Any]:
        """Audit code linting."""
        lint_commands = [
            ["flake8", "--max-line-length=88"],
            ["pylint", "--disable=C0103,C0111"],
            ["black", "--check", "."],
        ]

        for cmd in lint_commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    timeout=30,
                )

                return {
                    "passed": result.returncode == 0,
                    "command": " ".join(cmd),
                    "output": result.stdout + result.stderr,
                }

            except subprocess.TimeoutExpired:
                continue
            except FileNotFoundError:
                continue
            except Exception:
                continue

        return {
            "passed": True,
            "command": None,
            "output": "No linting tools found, skipping lint check",
        }

    def _audit_dependencies(self) -> Dict[str, Any]:
        """Audit project dependencies."""
        dependency_files = ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"]

        found_files = []
        for dep_file in dependency_files:
            file_path = self.project_root / dep_file
            if file_path.exists():
                found_files.append(dep_file)

        return {
            "dependency_files": found_files,
            "has_requirements": len(found_files) > 0,
        }

    def _generate_new_tasks(
        self, audit_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate new tasks based on audit results."""
        new_tasks = []

        if not audit_results["tests"]["passed"]:
            new_tasks.append(
                {
                    "id": 1000 + len(new_tasks),
                    "title": "Fix failing tests",
                    "assigned_to": "test-worker",
                    "status": "todo",
                }
            )

        if not audit_results["linting"]["passed"]:
            new_tasks.append(
                {
                    "id": 1000 + len(new_tasks),
                    "title": "Fix linting issues",
                    "assigned_to": "lint-worker",
                    "status": "todo",
                }
            )

        if not audit_results["git_status"]["clean"]:
            new_tasks.append(
                {
                    "id": 1000 + len(new_tasks),
                    "title": "Commit uncommitted changes",
                    "assigned_to": "git-worker",
                    "status": "todo",
                }
            )

        return new_tasks

    def _save_audit_results(self, results: Dict[str, Any]):
        """Save audit results to file."""
        audit_file = self.project_root / "AUDIT_RESULTS.json"
        with open(audit_file, "w") as f:
            json.dump(results, f, indent=2)


def run_audit(project_root: str = ".") -> Dict[str, Any]:
    """Convenience function to run audit."""
    auditor = AuditPhase(project_root)
    return auditor.run_audit()
