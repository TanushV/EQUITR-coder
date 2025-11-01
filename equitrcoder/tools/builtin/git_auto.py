"""
Automatic Git Commit Tool for checkpoints and planning phases
"""

import subprocess
from datetime import datetime
from pathlib import Path


class GitAutoCommit:
    """Handles automatic git commits at checkpoints and planning phases"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.enabled = self._check_git_repo()

    def _check_git_repo(self) -> bool:
        """Check if directory is a git repository"""
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def commit_all(self, message: str, allow_empty: bool = False) -> bool:
        """
        Commit all changes with given message
        Returns True if successful
        """
        if not self.enabled:
            print("⚠️  Not in a git repository, skipping commit")
            return False

        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True
            )

            # Check if there are changes to commit
            if not allow_empty:
                result = subprocess.run(
                    ["git", "diff", "--cached", "--quiet"],
                    cwd=self.repo_path,
                    capture_output=True,
                )
                if result.returncode == 0:
                    print("ℹ️  No changes to commit")
                    return True

            # Commit changes
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_message = f"{message}\n\nAuto-commit at {timestamp}"

            subprocess.run(
                ["git", "commit", "-m", full_message],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )

            print(f"✅ Committed: {message}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Git commit failed: {e}")
            return False

    def commit_planning_start(self) -> bool:
        """Commit at start of planning phase"""
        return self.commit_all("🎯 Start planning phase")

    def commit_planning_complete(self) -> bool:
        """Commit after planning documents are created"""
        return self.commit_all("📋 Planning phase complete - documents generated")

    def commit_checkpoint(self, task_title: str) -> bool:
        """Commit after completing a task/checkpoint"""
        safe_title = task_title.replace('"', "").replace("'", "")[:50]
        return self.commit_all(f"✅ Checkpoint: {safe_title}")

    def commit_task_start(self, task_title: str) -> bool:
        """Commit before starting a task"""
        safe_title = task_title.replace('"', "").replace("'", "")[:50]
        return self.commit_all(f"🚀 Starting: {safe_title}")

    def get_status(self) -> dict:
        """Get git repository status"""
        if not self.enabled:
            return {"enabled": False, "message": "Not a git repository"}

        try:
            # Get current branch
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            # Get last commit
            commit_result = subprocess.run(
                ["git", "log", "-1", "--oneline"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            # Get status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            return {
                "enabled": True,
                "branch": branch_result.stdout.strip(),
                "last_commit": commit_result.stdout.strip(),
                "changes": (
                    len(status_result.stdout.strip().split("\n"))
                    if status_result.stdout.strip()
                    else 0
                ),
            }

        except subprocess.CalledProcessError as e:
            return {"enabled": False, "message": f"Git error: {e}"}
