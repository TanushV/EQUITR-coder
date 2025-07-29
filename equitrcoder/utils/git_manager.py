"""Git management utilities for EQUITR Coder."""

import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GitManager:
    """Manages git operations for EQUITR Coder projects."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def is_git_repo(self) -> bool:
        """Check if the current directory is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def init_repo(self) -> bool:
        """Initialize a git repository if one doesn't exist."""
        if self.is_git_repo():
            logger.info("Git repository already exists")
            return True

        try:
            result = subprocess.run(
                ["git", "init"], cwd=self.repo_path, capture_output=True, text=True
            )
            if result.returncode == 0:
                logger.info("Git repository initialized")
                # Create initial .gitignore
                self._create_gitignore()
                return True
            else:
                logger.error(f"Failed to initialize git repository: {result.stderr}")
                return False
        except FileNotFoundError:
            logger.error("Git is not installed")
            return False

    def _create_gitignore(self):
        """Create a comprehensive .gitignore file for Python projects."""
        gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# EQUITR Coder specific
.equitr_sessions/
*.log
.equitr_cache/
"""
        gitignore_path = self.repo_path / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text(gitignore_content)
            logger.info("Created .gitignore file")

    def get_status(self) -> Dict[str, List[str]]:
        """Get git status information."""
        if not self.is_git_repo():
            return {"error": ["Not a git repository"]}

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return {"error": [result.stderr]}

            status = {"modified": [], "added": [], "deleted": [], "untracked": []}

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                status_code = line[:2]
                filename = line[3:]

                if status_code[0] == "M" or status_code[1] == "M":
                    status["modified"].append(filename)
                elif status_code[0] == "A":
                    status["added"].append(filename)
                elif status_code[0] == "D":
                    status["deleted"].append(filename)
                elif status_code[0] == "?":
                    status["untracked"].append(filename)

            return status

        except FileNotFoundError:
            return {"error": ["Git is not installed"]}

    def add_all(self) -> bool:
        """Add all changes to staging area."""
        if not self.is_git_repo():
            logger.error("Not a git repository")
            return False

        try:
            result = subprocess.run(
                ["git", "add", "-A"], cwd=self.repo_path, capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("All changes added to staging area")
                return True
            else:
                logger.error(f"Failed to add changes: {result.stderr}")
                return False

        except FileNotFoundError:
            logger.error("Git is not installed")
            return False

    def commit(self, message: str, auto_add: bool = True) -> bool:
        """Commit changes with a message."""
        if not self.is_git_repo():
            logger.error("Not a git repository")
            return False

        if auto_add:
            if not self.add_all():
                return False

        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info(f"Committed changes: {message}")
                return True
            else:
                # Check if there are no changes to commit
                if "nothing to commit" in result.stdout:
                    logger.info("No changes to commit")
                    return True
                else:
                    logger.error(f"Failed to commit: {result.stderr}")
                    return False

        except FileNotFoundError:
            logger.error("Git is not installed")
            return False

    def commit_task_completion(self, task_description: str) -> bool:
        """Commit changes with a standardized task completion message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = (
            f"Complete task: {task_description}\n\nCompleted at: {timestamp}"
        )

        return self.commit(commit_message)

    def get_recent_commits(self, count: int = 5) -> List[Dict[str, str]]:
        """Get recent commit information."""
        if not self.is_git_repo():
            return []

        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"-{count}",
                    "--pretty=format:%H|%s|%an|%ad",
                    "--date=short",
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return []

            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) >= 4:
                    commits.append(
                        {
                            "hash": parts[0][:8],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3],
                        }
                    )

            return commits

        except FileNotFoundError:
            return []

    def ensure_repo_ready(self) -> bool:
        """Ensure the repository is initialized and ready for commits."""
        if not self.is_git_repo():
            logger.info("Initializing git repository...")
            return self.init_repo()
        return True


def create_git_manager(repo_path: str = ".") -> GitManager:
    """Factory function to create a GitManager instance."""
    return GitManager(repo_path)
